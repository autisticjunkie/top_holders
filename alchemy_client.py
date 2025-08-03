import requests
import json
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AlchemyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = f"https://abstract-mainnet.g.alchemy.com/v2/{api_key}"
        self.chain_id = 2741
        
    def _make_request(self, method: str, params: List) -> Dict:
        """Make a JSON-RPC request to Alchemy API"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if "error" in data:
                logger.error(f"Alchemy API error: {data['error']}")
                raise Exception(f"Alchemy API error: {data['error']['message']}")
            
            return data.get("result", {})
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Failed to connect to Alchemy API: {str(e)}")
    
    def get_asset_transfers(self, contract_address: str) -> List[Dict]:
        """Get ALL ERC-20 transfers for a token using alchemy_getAssetTransfers"""
        transfers = []
        page_key = None
        
        while True:  # Keep fetching until no more pages
            params = [{
                "category": ["erc20"],
                "contractAddresses": [contract_address],
                "withMetadata": True,
                "excludeZeroValue": True,
                "maxCount": hex(1000)  # Max per page
            }]
            
            if page_key:
                params[0]["pageKey"] = page_key
            
            try:
                result = self._make_request("alchemy_getAssetTransfers", params)
                batch_transfers = result.get("transfers", [])
                transfers.extend(batch_transfers)
                
                page_key = result.get("pageKey")
                if not page_key or not batch_transfers:
                    break
                    
            except Exception as e:
                logger.warning(f"Error fetching transfers: {e}")
                break
        
        logger.info(f"Fetched {len(transfers)} total transfers")
        return transfers  # Return ALL transfers
    

    
    def get_token_metadata(self, contract_address: str) -> Dict:
        """Get token metadata using alchemy_getTokenMetadata"""
        params = [contract_address]
        return self._make_request("alchemy_getTokenMetadata", params)
    
    def calculate_token_balances(self, transfers: List[Dict]) -> Dict[str, int]:
        """Calculate token balances from transfer history"""
        balances = defaultdict(int)
        
        for transfer in transfers:
            from_addr = transfer.get("from", "").lower()
            to_addr = transfer.get("to", "").lower()
            value_hex = transfer.get("value", "0x0")
            
            # Convert value to int (handle both hex strings and numeric values)
            try:
                if isinstance(value_hex, str):
                    value = int(value_hex, 16) if value_hex.startswith("0x") else int(value_hex)
                elif isinstance(value_hex, (int, float)):
                    value = int(value_hex)
                else:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Skip zero address (minting/burning)
            if from_addr and from_addr != "0x0000000000000000000000000000000000000000":
                balances[from_addr] -= value
            
            if to_addr and to_addr != "0x0000000000000000000000000000000000000000":
                balances[to_addr] += value
        
        # Filter out negative or zero balances
        return {addr: balance for addr, balance in balances.items() if balance > 0}
    
    def get_top_holders(self, contract_address: str, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get top N holders of a token using transfer analysis"""
        try:
            logger.info(f"Fetching ALL transfers for token {contract_address}")
            transfers = self.get_asset_transfers(contract_address)
            
            if not transfers:
                logger.warning("No transfers found")
                return []
            
            logger.info(f"Found {len(transfers)} transfers")
            
            # Calculate balances from all transfers
            balances = self.calculate_token_balances(transfers)
            
            if not balances:
                logger.warning("No balances calculated")
                return []
            
            logger.info(f"Calculated {len(balances)} addresses with positive balances")
            
            # Sort by calculated balance and return top N
            sorted_holders = sorted(balances.items(), key=lambda x: x[1], reverse=True)
            
            logger.info(f"Found {len(sorted_holders)} total holders from transfer analysis")
            
            return sorted_holders[:top_n]
            
        except Exception as e:
            logger.error(f"Error getting top holders: {e}")
            raise
    
    def get_holder_other_tokens(self, address: str, exclude_token: str) -> list:
        """Get other significant token holdings for a wallet address using fast alchemy_getTokenBalances"""
        try:
            # Use the fast alchemy_getTokenBalances method - single API call!
            response = self._make_request("alchemy_getTokenBalances", [address, "erc20"])
            
            if not response or "result" not in response:
                return []
            
            token_balances = response["result"].get("tokenBalances", [])
            significant_tokens = []
            
            for token_data in token_balances:
                contract_addr = token_data.get("contractAddress", "").lower()
                balance_hex = token_data.get("tokenBalance", "0x0")
                
                # Convert hex balance to int
                try:
                    balance = int(balance_hex, 16)
                except (ValueError, TypeError):
                    continue
                
                # Skip the main token we're analyzing and zero balances
                if contract_addr == exclude_token.lower() or balance == 0:
                    continue
                
                try:
                    # Get token metadata
                    metadata = self.get_token_metadata(contract_addr)
                    if metadata:
                        symbol = metadata.get("symbol", "UNKNOWN")
                        decimals = metadata.get("decimals", 18)
                        
                        # Convert to readable balance
                        readable_balance = balance / (10 ** decimals)
                        
                        # Only include tokens with significant balances
                        is_significant = False
                        if symbol.upper() in ['ETH', 'WETH']:  # For ETH/WETH, 1+ is significant
                            is_significant = readable_balance >= 1.0
                        elif symbol.upper() in ['USDC', 'USDT', 'DAI']:  # For stablecoins, 1K+ is significant
                            is_significant = readable_balance >= 1000
                        else:  # For other tokens, 1M+ is significant (lowered threshold)
                            is_significant = readable_balance >= 1000000
                        
                        if is_significant:
                            significant_tokens.append({
                                "address": contract_addr,
                                "symbol": symbol,
                                "balance": readable_balance,
                                "raw_balance": balance
                            })
                except Exception as e:
                    # If metadata fails, only include if raw balance is very significant
                    if balance > 1000000 * (10 ** 18):  # Assume 18 decimals, 1M+ tokens
                        significant_tokens.append({
                            "address": contract_addr,
                            "symbol": "UNKNOWN",
                            "balance": balance / (10 ** 18),  # Assume 18 decimals
                            "raw_balance": balance
                        })
                    continue
            
            # Sort by raw balance and return top 10
            significant_tokens.sort(key=lambda x: x["raw_balance"], reverse=True)
            logger.info(f"Found {len(significant_tokens)} significant tokens for {address[:8]}...")
            return significant_tokens[:10]
            
        except Exception as e:
            logger.warning(f"Error fetching other tokens for {address}: {e}")
            return []
    
    def format_balance(self, balance: int, decimals: int = 18) -> str:
        """Format token balance to human readable string"""
        # Check if balance is already in human readable format (small numbers)
        if balance < 1e12:  # If balance is less than 1 trillion, it's likely already formatted
            readable_balance = balance
        else:
            # Convert from wei to human readable
            readable_balance = balance / (10 ** decimals)
        
        if readable_balance >= 1_000_000:
            return f"{readable_balance / 1_000_000:.2f}M"
        elif readable_balance >= 1_000:
            return f"{readable_balance / 1_000:.2f}K"
        else:
            return f"{readable_balance:.4f}".rstrip('0').rstrip('.')
    
    def shorten_address(self, address: str) -> str:
        """Shorten an Ethereum address for display"""
        if len(address) < 10:
            return address
        return f"{address[:6]}...{address[-4:]}"
    
    def is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if not address or not isinstance(address, str):
            return False
        
        # Remove 0x prefix if present
        if address.startswith("0x"):
            address = address[2:]
        
        # Check if it's 40 hex characters
        if len(address) != 40:
            return False
        
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
