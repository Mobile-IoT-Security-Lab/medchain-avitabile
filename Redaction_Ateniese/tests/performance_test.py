#!/usr/bin/env python3
"""
Performance Test Suite for Improved Redactable Blockchain
This test suite evaluates the performance of improved features under load:
- Smart contract deployment at scale
- Transaction processing with different types
- Redaction request handling
- Permission checking performance
"""

import sys
import os
import time
import statistics
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from InputsConfig import InputsConfig as p
from Models.SmartContract import SmartContract, ContractCall
from Models.Bitcoin.Node import Node
from Models.Transaction import Transaction
from Models.Block import Block


class PerformanceTestSuite:
    """Performance testing for improved blockchain features."""
    
    def __init__(self):
        self.results = {}
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Set up test nodes and environment."""
        print("Setting up performance test environment...")
        
        # Create test nodes
        self.admin = Node(id=1, hashPower=1000)
        self.admin.update_role("ADMIN")
        
        self.regulators = []
        for i in range(5):  # Multiple regulators
            regulator = Node(id=100 + i, hashPower=500)
            regulator.update_role("REGULATOR")
            self.regulators.append(regulator)
        
        self.miners = []
        for i in range(10):  # Multiple miners
            miner = Node(id=200 + i, hashPower=random.randint(100, 1000))
            miner.update_role("MINER")
            self.miners.append(miner)
        
        self.users = []
        for i in range(100):  # Many users
            user = Node(id=1000 + i, hashPower=0)
            user.update_role("USER")
            self.users.append(user)
        
        print(f"Created {len(self.users)} users, {len(self.miners)} miners, {len(self.regulators)} regulators")
    
    def time_function(self, func, *args, **kwargs):
        """Time a function execution."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def test_permission_checking_performance(self):
        """Test performance of permission checking system."""
        print("\n=== Testing Permission Checking Performance ===")
        
        actions = ["READ", "WRITE", "DEPLOY", "REDACT", "APPROVE", "AUDIT", "MINE", "TRANSACT"]
        times = []
        
        # Test permission checking for all users and all actions
        total_checks = len(self.users) * len(actions)
        
        start_time = time.time()
        for user in self.users:
            for action in actions:
                check_start = time.time()
                user.can_perform_action(action)
                check_end = time.time()
                times.append(check_end - check_start)
        
        total_time = time.time() - start_time
        
        avg_time = statistics.mean(times) * 1000  # Convert to milliseconds
        max_time = max(times) * 1000
        min_time = min(times) * 1000
        
        print(f"Permission checks completed: {total_checks}")
        print(f"Total time: {total_time:.3f} seconds")
        print(f"Average check time: {avg_time:.3f} ms")
        print(f"Min check time: {min_time:.3f} ms")
        print(f"Max check time: {max_time:.3f} ms")
        print(f"Checks per second: {total_checks / total_time:.0f}")
        
        self.results['permission_checks'] = {
            'total_checks': total_checks,
            'total_time': total_time,
            'avg_time_ms': avg_time,
            'checks_per_second': total_checks / total_time
        }
    
    def test_smart_contract_deployment_performance(self):
        """Test performance of smart contract deployment."""
        print("\n=== Testing Smart Contract Deployment Performance ===")
        
        contract_code = """
        contract TestContract {
            uint256 public value;
            mapping(address => uint256) public balances;
            
            function setValue(uint256 _value) public {
                value = _value;
            }
            
            function transfer(address to, uint256 amount) public {
                balances[msg.sender] -= amount;
                balances[to] += amount;
            }
        }
        """
        
        deployment_times = []
        num_deployments = 50
        
        print(f"Deploying {num_deployments} contracts...")
        
        for i in range(num_deployments):
            _, deploy_time = self.time_function(
                self.admin.deploy_contract,
                contract_code,
                "GENERAL"
            )
            deployment_times.append(deploy_time)
        
        avg_deploy_time = statistics.mean(deployment_times) * 1000
        max_deploy_time = max(deployment_times) * 1000
        min_deploy_time = min(deployment_times) * 1000
        total_deploy_time = sum(deployment_times)
        
        print(f"Contracts deployed: {num_deployments}")
        print(f"Total deployment time: {total_deploy_time:.3f} seconds")
        print(f"Average deployment time: {avg_deploy_time:.3f} ms")
        print(f"Min deployment time: {min_deploy_time:.3f} ms")
        print(f"Max deployment time: {max_deploy_time:.3f} ms")
        print(f"Deployments per second: {num_deployments / total_deploy_time:.2f}")
        
        self.results['contract_deployment'] = {
            'total_deployments': num_deployments,
            'total_time': total_deploy_time,
            'avg_time_ms': avg_deploy_time,
            'deployments_per_second': num_deployments / total_deploy_time
        }
    
    def test_transaction_creation_performance(self):
        """Test performance of creating different transaction types."""
        print("\n=== Testing Transaction Creation Performance ===")
        
        num_transactions = 1000
        transaction_types = ["TRANSFER", "CONTRACT_CALL", "CONTRACT_DEPLOY", "REDACTION_REQUEST"]
        
        creation_times = {}
        
        for tx_type in transaction_types:
            times = []
            print(f"Creating {num_transactions} {tx_type} transactions...")
            
            for i in range(num_transactions):
                start_time = time.time()
                
                if tx_type == "CONTRACT_CALL":
                    contract_call = ContractCall(
                        contract_address="0x1234567890abcdef",
                        function_name="transfer",
                        parameters=[100, "0xabcd"],
                        caller="0x123",
                        gas_limit=50000
                    )
                    tx = Transaction(
                        id=i,
                        sender=random.choice(self.users).id,
                        to=0,
                        tx_type=tx_type,
                        contract_call=contract_call
                    )
                elif tx_type == "REDACTION_REQUEST":
                    tx = Transaction(
                        id=i,
                        sender=random.choice(self.regulators).id,
                        to=0,
                        tx_type=tx_type,
                        metadata={
                            "target_block": random.randint(1, 100),
                            "target_tx": random.randint(0, 10),
                            "redaction_type": random.choice(["DELETE", "MODIFY", "ANONYMIZE"]),
                            "reason": "Compliance requirement"
                        }
                    )
                else:
                    tx = Transaction(
                        id=i,
                        sender=random.choice(self.users).id,
                        to=random.choice(self.users).id,
                        value=random.randint(1, 1000),
                        tx_type=tx_type
                    )
                
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times) * 1000
            total_time = sum(times)
            
            print(f"  Average creation time: {avg_time:.3f} ms")
            print(f"  Transactions per second: {num_transactions / total_time:.0f}")
            
            creation_times[tx_type] = {
                'avg_time_ms': avg_time,
                'total_time': total_time,
                'tx_per_second': num_transactions / total_time
            }
        
        self.results['transaction_creation'] = creation_times
    
    def test_block_processing_performance(self):
        """Test performance of processing blocks with different transaction types."""
        print("\n=== Testing Block Processing Performance ===")
        
        num_blocks = 100
        transactions_per_block = 50
        
        processing_times = []
        
        print(f"Processing {num_blocks} blocks with {transactions_per_block} transactions each...")
        
        for block_num in range(num_blocks):
            start_time = time.time()
            
            # Create block
            block = Block(
                depth=block_num,
                id=block_num * 1000,
                previous=(block_num - 1) * 1000 if block_num > 0 else -1,
                timestamp=int(time.time()),
                miner=random.choice(self.miners).id,
                block_type="NORMAL"
            )
            
            # Add transactions
            transactions = []
            for tx_num in range(transactions_per_block):
                tx_type = random.choice(["TRANSFER", "CONTRACT_CALL", "REDACTION_REQUEST"])
                
                if tx_type == "CONTRACT_CALL":
                    contract_call = ContractCall(
                        contract_address="0x1234567890abcdef",
                        function_name=random.choice(["transfer", "approve", "mint"]),
                        parameters=[random.randint(1, 1000)],
                        caller=str(random.choice(self.users).id),
                        gas_limit=random.randint(30000, 100000)
                    )
                    tx = Transaction(
                        id=block_num * 1000 + tx_num,
                        tx_type=tx_type,
                        contract_call=contract_call
                    )
                else:
                    tx = Transaction(
                        id=block_num * 1000 + tx_num,
                        sender=random.choice(self.users).id,
                        to=random.choice(self.users).id,
                        value=random.randint(1, 1000),
                        tx_type=tx_type
                    )
                
                transactions.append(tx)
            
            block.transactions = transactions
            
            # Process block (simulate validation)
            is_redactable = block.is_redactable()
            contract_state = block.get_smart_contract_state()
            
            end_time = time.time()
            processing_times.append(end_time - start_time)
        
        avg_processing_time = statistics.mean(processing_times) * 1000
        max_processing_time = max(processing_times) * 1000
        min_processing_time = min(processing_times) * 1000
        total_processing_time = sum(processing_times)
        
        total_transactions = num_blocks * transactions_per_block
        
        print(f"Blocks processed: {num_blocks}")
        print(f"Total transactions: {total_transactions}")
        print(f"Total processing time: {total_processing_time:.3f} seconds")
        print(f"Average block processing time: {avg_processing_time:.3f} ms")
        print(f"Min block processing time: {min_processing_time:.3f} ms")
        print(f"Max block processing time: {max_processing_time:.3f} ms")
        print(f"Blocks per second: {num_blocks / total_processing_time:.2f}")
        print(f"Transactions per second: {total_transactions / total_processing_time:.0f}")
        
        self.results['block_processing'] = {
            'blocks_processed': num_blocks,
            'total_transactions': total_transactions,
            'total_time': total_processing_time,
            'avg_block_time_ms': avg_processing_time,
            'blocks_per_second': num_blocks / total_processing_time,
            'transactions_per_second': total_transactions / total_processing_time
        }
    
    def test_redaction_workflow_performance(self):
        """Test performance of redaction request and approval workflow."""
        print("\n=== Testing Redaction Workflow Performance ===")
        
        num_requests = 100
        
        request_times = []
        approval_times = []
        
        print(f"Processing {num_requests} redaction requests...")
        
        for i in range(num_requests):
            # Create redaction request
            regulator = random.choice(self.regulators)
            
            start_time = time.time()
            request_id = regulator.request_redaction(
                target_block=random.randint(1, 100),
                target_tx=random.randint(0, 10),
                redaction_type=random.choice(["DELETE", "MODIFY", "ANONYMIZE"]),
                reason="Performance test redaction"
            )
            end_time = time.time()
            
            if request_id:
                request_times.append(end_time - start_time)
                
                # Process approvals
                approvers = [self.admin] + random.sample(self.regulators, 2)
                
                for approver in approvers:
                    start_time = time.time()
                    approver.vote_on_redaction(request_id, True, "Performance test approval")
                    end_time = time.time()
                    approval_times.append(end_time - start_time)
        
        if request_times:
            avg_request_time = statistics.mean(request_times) * 1000
            total_request_time = sum(request_times)
            
            print(f"Redaction requests created: {len(request_times)}")
            print(f"Average request creation time: {avg_request_time:.3f} ms")
            print(f"Requests per second: {len(request_times) / total_request_time:.2f}")
        
        if approval_times:
            avg_approval_time = statistics.mean(approval_times) * 1000
            total_approval_time = sum(approval_times)
            
            print(f"Approvals processed: {len(approval_times)}")
            print(f"Average approval time: {avg_approval_time:.3f} ms")
            print(f"Approvals per second: {len(approval_times) / total_approval_time:.0f}")
        
        self.results['redaction_workflow'] = {
            'requests_created': len(request_times),
            'approvals_processed': len(approval_times),
            'avg_request_time_ms': avg_request_time if request_times else 0,
            'avg_approval_time_ms': avg_approval_time if approval_times else 0
        }
    
    def run_all_performance_tests(self):
        """Run all performance tests."""
        print("Improved Redactable Blockchain - Performance Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        self.test_permission_checking_performance()
        self.test_smart_contract_deployment_performance()
        self.test_transaction_creation_performance()
        self.test_block_processing_performance()
        self.test_redaction_workflow_performance()
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        print(f"Total test time: {total_time:.2f} seconds")
        print()
        
        # Summary of key metrics
        if 'permission_checks' in self.results:
            print(f"Permission checks/sec: {self.results['permission_checks']['checks_per_second']:.0f}")
        
        if 'contract_deployment' in self.results:
            print(f"Contract deployments/sec: {self.results['contract_deployment']['deployments_per_second']:.2f}")
        
        if 'block_processing' in self.results:
            print(f"Block processing/sec: {self.results['block_processing']['blocks_per_second']:.2f}")
            print(f"Transaction processing/sec: {self.results['block_processing']['transactions_per_second']:.0f}")
        
        # Check for performance issues
        print("\nPERFORMANCE ASSESSMENT:")
        issues = []
        
        if 'permission_checks' in self.results:
            if self.results['permission_checks']['checks_per_second'] < 1000:
                issues.append("Permission checking might be slow for high-load scenarios")
        
        if 'contract_deployment' in self.results:
            if self.results['contract_deployment']['deployments_per_second'] < 1:
                issues.append("Contract deployment is slow - consider optimization")
        
        if 'block_processing' in self.results:
            if self.results['block_processing']['transactions_per_second'] < 100:
                issues.append("Transaction processing throughput may be insufficient")
        
        if issues:
            print("⚠️  Performance issues detected:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ All performance metrics are within acceptable ranges")
        
        print("\n🔍 Use these results to identify bottlenecks and optimization opportunities.")
        
        return self.results


def main():
    """Run the performance test suite."""
    suite = PerformanceTestSuite()
    results = suite.run_all_performance_tests()
    return results


if __name__ == "__main__":
    main()
