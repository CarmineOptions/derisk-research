from src.collectors.loan_state.nostra import NostraLoanStateCollector

class LoanStateManager:
    def __init__(self):
        self.collectors = {
            "nostra_mainnet": NostraLoanStateCollector("nostra_mainnet"),
            # Outros coletores...
        }

    async def collect_all(self):
        results = {}
        for network, collector in self.collectors.items():
            results[network] = await collector.collect()
        return results
