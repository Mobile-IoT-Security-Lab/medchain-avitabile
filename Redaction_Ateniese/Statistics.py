from InputsConfig import InputsConfig as p
from Models.Consensus import Consensus as c
from Models.Incentives import Incentives
import pandas as pd
import os
from openpyxl import load_workbook


class Statistics:
    # Global variables used to calculate and print stimulation results
    totalBlocks = 0
    mainBlocks = 0
    staleBlocks = 0
    staleRate = 0
    blockData = []
    blocksResults = []
    blocksSize = []
    profits = [[0 for x in range(7)] for y in
               range(p.Runs * len(p.NODES))]  # rows number of miners * number of runs, columns =7
    index = 0
    original_chain = []
    chain = []
    redactResults = []
    allRedactRuns = []
    round = 0
    
    # Enhanced statistics for smart contracts and permissions
    smartContractData = []
    contractCalls = 0
    contractDeployments = 0
    redactionRequests = 0
    redactionApprovals = 0
    redactionRejections = 0
    permissionViolations = 0
    privacyPolicyEnforcements = 0
    
    # Detailed redaction statistics
    redactionsByType = {"DELETE": 0, "MODIFY": 0, "ANONYMIZE": 0}
    redactionsByRole = {"ADMIN": 0, "REGULATOR": 0, "MINER": 0, "USER": 0}
    redactionTimestamps = []
    averageRedactionTime = 0

    def calculate(t):
        Statistics.global_chain()  # print the global chain
        Statistics.blocks_results(t)  # calculate and print block statistics e.g., # of accepted blocks and stale rate etc
        if p.hasRedact:
            Statistics.redact_result()  # to calculate the info per redact operation
        
        # Calculate smart contract statistics
        if hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:
            Statistics.smart_contract_results()
        
        # Calculate permission and redaction statistics
        if hasattr(p, 'hasPermissions') and p.hasPermissions:
            Statistics.permission_results()
    
    @staticmethod
    def smart_contract_results():
        """Calculate smart contract related statistics."""
        Statistics.contractCalls = 0
        Statistics.contractDeployments = 0
        
        # Count smart contract transactions across all blocks
        for block in c.global_chain:
            for tx in block.transactions:
                if hasattr(tx, 'tx_type'):
                    if tx.tx_type == "CONTRACT_CALL":
                        Statistics.contractCalls += 1
                    elif tx.tx_type == "CONTRACT_DEPLOY":
                        Statistics.contractDeployments += 1
        
        # Collect contract call data
        for block in c.global_chain:
            if hasattr(block, 'contract_calls'):
                for call in block.contract_calls:
                    contract_data = [
                        block.depth,
                        call.contract_address,
                        call.function_name,
                        call.gas_used,
                        call.success
                    ]
                    Statistics.smartContractData.append(contract_data)
        
        print(f"Smart Contract Statistics:")
        print(f"  Total Contract Calls: {Statistics.contractCalls}")
        print(f"  Total Contract Deployments: {Statistics.contractDeployments}")
        print(f"  Deployed Contracts: {len(p.DEPLOYED_CONTRACTS) if hasattr(p, 'DEPLOYED_CONTRACTS') else 0}")
    
    @staticmethod
    def permission_results():
        """Calculate permission and redaction related statistics."""
        Statistics.redactionRequests = 0
        Statistics.redactionApprovals = 0
        Statistics.redactionRejections = 0
        
        # Reset counters
        Statistics.redactionsByType = {"DELETE": 0, "MODIFY": 0, "ANONYMIZE": 0}
        Statistics.redactionsByRole = {"ADMIN": 0, "REGULATOR": 0, "MINER": 0, "USER": 0}
        Statistics.redactionTimestamps = []
        
        for node in p.NODES:
            # Count redaction requests
            Statistics.redactionRequests += len(node.redaction_requests)
            
            # Analyze redaction requests by status
            for request in node.redaction_requests:
                if request["status"] == "APPROVED":
                    Statistics.redactionApprovals += 1
                    redaction_type = request.get("redaction_type", "DELETE")
                    if redaction_type in Statistics.redactionsByType:
                        Statistics.redactionsByType[redaction_type] += 1
                    
                    # Track by requester role
                    requester_role = getattr(node, 'role', 'USER')
                    if requester_role in Statistics.redactionsByRole:
                        Statistics.redactionsByRole[requester_role] += 1
                    
                    Statistics.redactionTimestamps.append(request["timestamp"])
                    
                elif request["status"] == "REJECTED":
                    Statistics.redactionRejections += 1
        
        # Calculate average redaction time
        if Statistics.redactionTimestamps:
            import time
            current_time = time.time()
            redaction_times = [current_time - ts for ts in Statistics.redactionTimestamps]
            Statistics.averageRedactionTime = sum(redaction_times) / len(redaction_times)
        
        print(f"Permission & Redaction Statistics:")
        print(f"  Total Redaction Requests: {Statistics.redactionRequests}")
        print(f"  Approved Redactions: {Statistics.redactionApprovals}")
        print(f"  Rejected Redactions: {Statistics.redactionRejections}")
        print(f"  Redactions by Type: {Statistics.redactionsByType}")
        print(f"  Redactions by Role: {Statistics.redactionsByRole}")
        if Statistics.averageRedactionTime > 0:
            print(f"  Average Redaction Processing Time: {Statistics.averageRedactionTime:.2f} seconds")

    # Calculate block statistics Results
    def blocks_results(t):
        trans = 0
        Statistics.mainBlocks = len(c.global_chain) - 1
        Statistics.staleBlocks = Statistics.totalBlocks - Statistics.mainBlocks
        for b in c.global_chain:
            trans += len(b.transactions)
        Statistics.staleRate = round(Statistics.staleBlocks / Statistics.totalBlocks * 100, 2)
        Statistics.blockData = [Statistics.totalBlocks, Statistics.mainBlocks, Statistics.staleBlocks, Statistics.staleRate, trans, t, str(Statistics.blocksSize)]
        Statistics.blocksResults += [Statistics.blockData]

    ############################ Calculate and distibute rewards among the miners #############################
    def profit_results(self):

        for m in p.NODES:
            i = Statistics.index + m.id * p.Runs
            Statistics.profits[i][0] = m.id
            Statistics.profits[i][1] = m.hashPower
            Statistics.profits[i][2] = m.blocks
            Statistics.profits[i][3] = round(m.blocks / Statistics.mainBlocks * 100, 2)
            Statistics.profits[i][4] = 0
            Statistics.profits[i][5] = 0
            Statistics.profits[i][6] = m.balance
        #print("Profits :")
        #print(Statistics.profits)

        Statistics.index += 1

    ########################################################### prepare the global chain  ###########################################################################################
    def global_chain():
        for i in c.global_chain:
            block = [i.depth, i.id, i.previous, i.timestamp, i.miner, len(i.transactions), i.size]
            Statistics.chain += [block]
        print("Length of CHAIN = "+str(len(Statistics.chain)))
        # print(Statistics.chain)


    def original_global_chain():
        for i in c.global_chain:
            block = [i.depth, i.id, i.previous, i.timestamp, i.miner, len(i.transactions), str(i.size)]
            Statistics.original_chain += [block]


    ########################################################## generate redaction data ############################################################
    def redact_result():
        i = 0
        profit_count, op_count = 0, p.redactRuns
        while i < len(p.NODES):
            if p.redactRuns == 0:
                profit_count = 0
            if len(p.NODES[i].redacted_tx) != 0 and p.redactRuns > 0:
                for j in range(len(p.NODES[i].redacted_tx)):
                    print(f'Deletion/Redaction: Block Depth => {p.NODES[i].redacted_tx[j][0]}, Transaction ID => {p.NODES[i].redacted_tx[j][1].id}')
                    # Added Miner ID,Block Depth,Transaction ID,Redaction Profit,Performance Time (ms),Blockchain Length,# of Tx
                    result = [p.NODES[i].id, p.NODES[i].redacted_tx[j][0], p.NODES[i].redacted_tx[j][1].id,
                              p.NODES[i].redacted_tx[j][2], p.NODES[i].redacted_tx[j][3],
                              p.NODES[i].redacted_tx[j][4], p.NODES[i].redacted_tx[j][5]]
                    profit_count += p.NODES[i].redacted_tx[j][2]
                    Statistics.redactResults.append(result)
            i += 1
        Statistics.allRedactRuns.append([profit_count, op_count])

    ########################################################### Print simulation results to Excel ###########################################################################################
    def print_to_excel(fname):

        df1 = pd.DataFrame(
            {'Block Time': [p.Binterval], 'Block Propagation Delay': [p.Bdelay], 'No. Miners': [len(p.NODES)],
             'Simulation Time': [p.simTime]})
        # data = {'Stale Rate': Results.staleRate,'# Stale Blocks': Results.staleBlocks,'# Total Blocks': Results.totalBlocks, '# Included Blocks': Results.mainBlocks}

        df2 = pd.DataFrame(Statistics.blocksResults)
        df2.columns = ['Total Blocks', 'Main Blocks', 'Stale Blocks', 'Stale Rate',
                       '# transactions', 'Performance Time', 'Block sizeeeeeee']

        # df3 = pd.DataFrame(Statistics.profits)
        # df3.columns = ['Miner ID', '% Hash Power', '# Mined Blocks', '% of main blocks', '# Uncle Blocks',
        #  '% of uncles', 'Profit (in ETH)']

        df4 = pd.DataFrame(Statistics.chain)
        print(df4)
        # df4.columns= ['Block Depth', 'Block ID', 'Previous Block', 'Block Timestamp', 'Miner ID', '# transactions','Block Size']
        df4.columns = ['Block Depth', 'Block ID', 'Previous Block', 'Block Timestamp', 'Miner ID', '# transactions',
                           'Block Size']

        if p.hasRedact:
            if p.redactRuns > 0:
                # blockchain history before redaction
                df7 = pd.DataFrame(Statistics.original_chain)
                # df4.columns= ['Block Depth', 'Block ID', 'Previous Block', 'Block Timestamp', 'Miner ID', '# transactions','Block Size']
                df7.columns = ['Block Depth', 'Block ID', 'Previous Block', 'Block Timestamp', 'Miner ID',
                                   '# transactions',
                                   'Block Size']

                # Redaction results
                df5 = pd.DataFrame(Statistics.redactResults)
                print(df5)
                df5.columns = ['Miner ID', 'Block Depth', 'Transaction ID', 'Redaction Profit', 'Performance Time (ms)', 'Blockchain Length', '# of Tx']

            df6 = pd.DataFrame(Statistics.allRedactRuns)
            print(df6)
            df6.columns = ['Total Profit/Cost', 'Redact op runs']
        writer = pd.ExcelWriter(fname, engine='xlsxwriter')
        df1.to_excel(writer, sheet_name='InputConfig')
        df2.to_excel(writer, sheet_name='SimOutput')
        # df3.to_excel(writer, sheet_name='Profit')
        
        # Add smart contract statistics
        if hasattr(p, 'hasSmartContracts') and p.hasSmartContracts and Statistics.smartContractData:
            df_contracts = pd.DataFrame(Statistics.smartContractData)
            df_contracts.columns = ['Block Depth', 'Contract Address', 'Function Name', 'Gas Used', 'Success']
            df_contracts.to_excel(writer, sheet_name='SmartContracts')
            
            # Smart contract summary
            contract_summary = [
                ['Total Contract Calls', Statistics.contractCalls],
                ['Total Contract Deployments', Statistics.contractDeployments],
                ['Deployed Contracts', len(p.DEPLOYED_CONTRACTS) if hasattr(p, 'DEPLOYED_CONTRACTS') else 0]
            ]
            df_contract_summary = pd.DataFrame(contract_summary)
            df_contract_summary.columns = ['Metric', 'Value']
            df_contract_summary.to_excel(writer, sheet_name='ContractSummary')
        
        # Add permission and redaction statistics
        if hasattr(p, 'hasPermissions') and p.hasPermissions:
            permission_summary = [
                ['Total Redaction Requests', Statistics.redactionRequests],
                ['Approved Redactions', Statistics.redactionApprovals],
                ['Rejected Redactions', Statistics.redactionRejections],
                ['Average Redaction Time (s)', Statistics.averageRedactionTime],
                ['DELETE Redactions', Statistics.redactionsByType.get('DELETE', 0)],
                ['MODIFY Redactions', Statistics.redactionsByType.get('MODIFY', 0)],
                ['ANONYMIZE Redactions', Statistics.redactionsByType.get('ANONYMIZE', 0)],
                ['ADMIN Redactions', Statistics.redactionsByRole.get('ADMIN', 0)],
                ['REGULATOR Redactions', Statistics.redactionsByRole.get('REGULATOR', 0)],
                ['MINER Redactions', Statistics.redactionsByRole.get('MINER', 0)],
                ['USER Redactions', Statistics.redactionsByRole.get('USER', 0)]
            ]
            df_permissions = pd.DataFrame(permission_summary)
            df_permissions.columns = ['Metric', 'Value']
            df_permissions.to_excel(writer, sheet_name='PermissionStats')
        
        if p.hasRedact and p.redactRuns > 0:
            df2.to_csv('Results/time_redact.csv', sep=',', mode='a+', index=False, header=False, encoding='utf-8')
            df7.to_excel(writer, sheet_name='ChainBeforeRedaction')
            df5.to_excel(writer, sheet_name='RedactResult')
            df4.to_excel(writer, sheet_name='Chain')
            # Add the result to transaction/performance time csv to statistic analysis
            # df5.to_csv('Results_new/tx_time.csv', sep=',', mode='a+', index=False, header=False,encoding='utf-8')
            # Add the result to block length/performance time csv to statistic analysis, and fixed the number of transactions
            df5.to_csv('Results/block_time.csv', sep=',', mode='a+', index=False, header=False,encoding='utf-8')
            if p.hasMulti:
                df5.to_csv('Results/block_time_den.csv', sep=',', mode='a+', index=False, header=False)
                df5.to_csv('Results/tx_time_den.csv', sep=',', mode='a+', index=False, header=False)
            # Add the total profit earned vs the number of redaction operation runs
            df6.to_csv('Results/profit_redactRuns.csv', sep=',', mode='a+', index=False, header=False)
        else:
            df4.to_excel(writer, sheet_name='Chain')
            df2.to_csv('Results/time.csv', sep=',', mode='a+', index=False, header=False)
        writer.save()


    ########################################################### Reset all global variables used to calculate the simulation results ###########################################################################################
    def reset():
        Statistics.totalBlocks = 0
        Statistics.mainBlocks = 0
        Statistics.staleBlocks = 0
        Statistics.staleRate = 0
        Statistics.blockData = []
        
        # Reset enhanced statistics
        Statistics.smartContractData = []
        Statistics.contractCalls = 0
        Statistics.contractDeployments = 0
        Statistics.redactionRequests = 0
        Statistics.redactionApprovals = 0
        Statistics.redactionRejections = 0
        Statistics.permissionViolations = 0
        Statistics.privacyPolicyEnforcements = 0
        Statistics.redactionsByType = {"DELETE": 0, "MODIFY": 0, "ANONYMIZE": 0}
        Statistics.redactionsByRole = {"ADMIN": 0, "REGULATOR": 0, "MINER": 0, "USER": 0}
        Statistics.redactionTimestamps = []
        Statistics.averageRedactionTime = 0

    def reset2():
        Statistics.blocksResults = []
        Statistics.profits = [[0 for x in range(7)] for y in
                              range(p.Runs * len(p.NODES))]  # rows number of miners * number of runs, columns =7
        Statistics.index = 0
        Statistics.chain = []
        Statistics.redactResults = []
        Statistics.allRedactRuns = []
