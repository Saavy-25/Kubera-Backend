from datetime import datetime, timedelta

class DashboardManager:
    def __init__(self):
       pass
    
    def update_dashboard(self, dashboard, scanned_receipt):
        self.__update_weekly_spending(dashboard, scanned_receipt.date, scanned_receipt.total_receipt_price)
        self.__update_monthly_spending(dashboard, scanned_receipt.date, scanned_receipt.total_receipt_price)
        self.__update_yearly_spending(dashboard, scanned_receipt.date, scanned_receipt.total_receipt_price)

        self.__update_average_grocery_run_cost(dashboard, scanned_receipt)
        self.__update_favorite_item_of_the_month(dashboard, scanned_receipt)
        self.__update_most_expensive_item(dashboard, scanned_receipt)

    def __update_weekly_spending(self, dashboard, receipt_date, total_price):
        receipt_date = datetime.strptime(receipt_date, '%Y-%m-%d').date()

        # find the first day of the week (Monday)
        start_of_week = receipt_date - timedelta(days=receipt_date.weekday())
        start_of_week_key = start_of_week.isoformat()

        # update or add weekly spending to dashboard
        if start_of_week_key in dashboard.weekly_spending:
            dashboard.weekly_spending[start_of_week_key] += total_price
        else:
            dashboard.weekly_spending[start_of_week_key] = total_price

    def __update_monthly_spending(self, dashboard, receipt_date, total_price):
        receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
    
        # get date in format "YYYY-MM"
        month_key = receipt_date.strftime("%Y-%m")
        
        # update or add the monthly spending to dashboard
        if month_key in dashboard.monthly_spending:
            dashboard.monthly_spending[month_key] += total_price
        else:
            dashboard.monthly_spending[month_key] = total_price

    def __update_yearly_spending(self, dashboard, receipt_date, total_price):
        # get date in format "YYYY"
        receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
        year_key = str(receipt_date.year)
        
        # update or add the monthly spending to dashboard
        if year_key in dashboard.yearly_spending:
            dashboard.yearly_spending[year_key] += total_price
        else:
            dashboard.yearly_spending[year_key] = total_price

    def __update_average_grocery_run_cost(self, dashboard, scanned_receipt):
        dashboard.total_runs = dashboard.total_runs or 0
        
        # calculate and update average
        dashboard.average_grocery_run_cost = ((dashboard.average_grocery_run_cost * dashboard.total_runs) + scanned_receipt.total_receipt_price) / (dashboard.total_runs + 1)
        
        # update total runs
        dashboard.total_runs += 1

    def __update_favorite_item_of_the_month(self, dashboard, scanned_receipt):
        # only update if the receipt is from the current month
        receipt_month = scanned_receipt.date[:7]
        current_month = datetime.today().strftime("%Y-%m")

        if receipt_month != current_month:
            return  

        self.__update_item_frequency(dashboard, scanned_receipt)

        # find the most frequent item
        most_frequent_id = max(
            dashboard.current_month_item_frequency,
            key=dashboard.current_month_item_frequency.get
        )
        frequency = dashboard.current_month_item_frequency[most_frequent_id]

        for favorite in dashboard.favorite_items:
            if favorite["date"] == current_month: # find current month
                # just update frequency if same item
                if favorite["name"] == most_frequent_id:
                    favorite["frequency"] = frequency
                else:
                    # update the genericId and frequency
                    favorite["name"] = most_frequent_id
                    favorite["frequency"] = frequency
                return

        # if no favorite exists for current month, add it
        dashboard.favorite_items.insert(0, {
            "date": current_month,
            "name": most_frequent_id,
            "frequency": frequency
    })

    def __update_item_frequency(self, dashboard, scanned_receipt):
        for item in scanned_receipt.scanned_line_items:           
            if item.generic_id:
                dashboard.current_month_item_frequency[item.generic_id] = (
                    dashboard.current_month_item_frequency.get(item.generic_id, 0) + 1
                )

    def __update_most_expensive_item(self, dashboard, scanned_receipt):
        # only update if the receipt is from the current month
        receipt_month = scanned_receipt.date[:7]
        current_month = datetime.today().strftime("%Y-%m")

        if receipt_month != current_month:
            return
        
        most_expensive_item = dashboard.most_expensive_item or {
            "name": "", 
            "price": 0, 
            "date": current_month
        }

        # iterate through receipt line items
        for item in scanned_receipt.scanned_line_items:
            # update most expensive item if a more expensive item is found
            if item.price_per_count is not None and item.price_per_count > most_expensive_item["price"]:
                most_expensive_item = {
                    "name": item.generic_id,
                    "price": item.price_per_count,
                    "date": receipt_month
                }

        # update dashboard
        dashboard.most_expensive_item = most_expensive_item