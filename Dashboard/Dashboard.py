class Dashboard:
    def __init__(self, username, weeklySpending=None, monthlySpending=None, yearlySpending=None,
                 averageGroceryRunCost=0, totalRuns=0, mostExpensiveItem=None, 
                 favoriteItems=None, currentMonthItemFrequency=None):
        self.username = username
        self.weekly_spending = weeklySpending or {}
        self.monthly_spending = monthlySpending or {}
        self.yearly_spending = yearlySpending or {}
        self.average_grocery_run_cost = averageGroceryRunCost
        self.total_runs = totalRuns
        self.most_expensive_item = mostExpensiveItem or {}
        self.favorite_items = favoriteItems or []
        self.current_month_item_frequency = currentMonthItemFrequency or {}

    def flutter_response(self):
        """convert model to map for use in frontend response."""
        # favorite_response = {}
        # for item in self.favorite_items:
        #     item['name'] = str(item['name'])
        
        # expensive_response = {}
        # for key, value in self.most_expensive_item.items():
        #     expensive_response[str(key)] = value

        return {
            "username": self.username,
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
            "username": self.username,
            "weeklySpending": self.weekly_spending,
            "monthlySpending": self.monthly_spending,
            "yearlySpending": self.yearly_spending,
            "averageGroceryRunCost": self.average_grocery_run_cost,
            "totalRuns": self.total_runs,
            "mostExpensiveItem": self.most_expensive_item,
            "favoriteItems": self.favorite_items,
            "currentMonthItemFrequency": self.current_month_item_frequency
        }
