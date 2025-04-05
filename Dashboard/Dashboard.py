class Dashboard:
    def __init__(self, user_id, weekly_spending=None, monthly_spending=None, yearly_spending=None,
                 average_grocery_run_cost=0, total_runs=0, most_expensive_item=None, 
                 favorite_items=None, current_month_item_frequency=None):
        self._user_id = user_id
        self.weekly_spending = weekly_spending or {}
        self.monthly_spending = monthly_spending or {}
        self.yearly_spending = yearly_spending or {}
        self.average_grocery_run_cost = average_grocery_run_cost
        self.total_runs = total_runs
        self.most_expensive_item = most_expensive_item or {}
        self.favorite_items = favorite_items or []
        self.current_month_item_frequency = current_month_item_frequency or {}

    def flutter_response(self):
        """convert model to map for use in frontend response."""
        return {
            "userId": self._user_id,
            "weeklySpending": self.weekly_spending,
            "monthlySpending": self.monthly_spending,
            "yearlySpending": self.yearly_spending,
            "averageGroceryRunCost": self.average_grocery_run_cost,
            "totalRuns": self.total_runs,
            "mostExpensiveItem": self.most_expensive_item,
            "favoriteItems": self.favorite_items,
            "currentMonthItemFrequency": self.current_month_item_frequency
        }

    def get_mongo_entry(self):
        """convert model to map for use in MongoDB."""
        return {
            "userId": self._user_id,
            "weeklySpending": self.weekly_spending,
            "monthlySpending": self.monthly_spending,
            "yearlySpending": self.yearly_spending,
            "averageGroceryRunCost": self.average_grocery_run_cost,
            "totalRuns": self.total_runs,
            "mostExpensiveItem": self.most_expensive_item,
            "favoriteItems": self.favorite_items,
            "currentMonthItemFrequency": self.current_month_item_frequency
        }
