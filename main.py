import requests

class NutritionAnalyzer:
    def __init__(self):
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.api_key = "DEMO_KEY"
        self.saved_foods = []

    def search_food(self, food_name):
        # Search for a food item in the USDA database
        endpoint = f"{self.base_url}/foods/search"
        params = {
            "query": food_name,
            "api_key": self.api_key,
            "dataType": "Foundation,SR Legacy",
            "pageSize": 5
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

    def extract_nutrients(self, food_data):
        # Map of nutrients we care about
        nutrients_map = {
            "Protein": "g",
            "Total lipid (fat)": "g",
            "Carbohydrate, by difference": "g",
            "Fiber, total dietary": "g",
            "Sugars, total including NLEA": "g",
            "Energy": "kcal",
            "Calcium, Ca": "mg",
            "Iron, Fe": "mg",
            "Sodium, Na": "mg",
            "Vitamin C, total ascorbic acid": "mg"
        }

        nutrition_info = {}

        # Loop through and grab what we need
        for nutrient in food_data.get("foodNutrients", []):
            nutrient_name = nutrient.get("nutrientName")
            if nutrient_name in nutrients_map:
                value = nutrient.get("value", 0)
                unit = nutrient.get("unitName", nutrients_map[nutrient_name])
                nutrition_info[nutrient_name] = {"value": value, "unit": unit}

        return nutrition_info

    def display_results(self, food_name, foods_list):
        """Show nutrition info in a nice readable format"""
        if not foods_list:
            print(f"\nNo results found for '{food_name}'. Try a different search term.")
            return

        print(f"\n{'=' * 60}")
        print(f"Nutrition Results for: {food_name}")
        print(f"{'=' * 60}\n")

        # Show top 3 results
        for idx, food in enumerate(foods_list[:3], 1):
            food_description = food.get("description", "Unknown")
            print(f"{idx}. {food_description}")
            print(f"   Serving Size: 100g")
            print("-" * 60)

            nutrients = self.extract_nutrients(food)

            if nutrients:
                for nutrient_name, info in nutrients.items():
                    # Clean up the nutrient names for display
                    display_name = nutrient_name.replace(", total dietary", "") \
                        .replace(", by difference", "") \
                        .replace(", total including NLEA", "") \
                        .replace("Total lipid (fat)", "Fat")
                    value = info["value"]
                    unit = info["unit"]
                    print(f"   {display_name:<30}: {value:>8.2f} {unit}")
            else:
                print("   No detailed nutrition data available")

            print()

    def save_food_for_comparison(self, food_name, foods_list):
        """Let user pick which food item to save for comparing later"""
        if not foods_list:
            print(f"\nCannot save '{food_name}' - no data found.")
            return False

        print(f"\nSelect which item to save for comparison:")
        for idx, food in enumerate(foods_list[:3], 1):
            print(f"{idx}. {food.get('description', 'Unknown')}")

        try:
            choice = input("\nEnter number (or press Enter to skip): ").strip()
            if not choice:
                return False

            choice_idx = int(choice) - 1
            if 0 <= choice_idx < min(3, len(foods_list)):
                selected_food = foods_list[choice_idx]
                food_info = {
                    "name": selected_food.get("description", "Unknown"),
                    "nutrients": self.extract_nutrients(selected_food)
                }
                self.saved_foods.append(food_info)
                print(f"✓ Saved '{food_info['name']}' for comparison!")
                return True
            else:
                print("Invalid selection.")
                return False
        except (ValueError, IndexError):
            print("Invalid input.")
            return False

    def compare_foods(self):
        # Need at least 2 foods to make a comparison
        if len(self.saved_foods) < 2:
            print(f"\nYou need at least 2 foods to compare. Currently saved: {len(self.saved_foods)}")
            return

        print(f"\n{'=' * 80}")
        print(" " * 25 + "FOOD COMPARISON")
        print(f"{'=' * 80}\n")

        print(f"Comparing {len(self.saved_foods)} foods (per 100g serving):\n")

        for idx, food in enumerate(self.saved_foods, 1):
            print(f"{idx}. {food['name']}")
        print()

        # Get all unique nutrients across all foods
        all_nutrient_names = set()
        for food in self.saved_foods:
            all_nutrient_names.update(food['nutrients'].keys())

        # Better names for display
        nutrient_display_names = {
            "Protein": "Protein",
            "Total lipid (fat)": "Fat",
            "Carbohydrate, by difference": "Carbohydrate",
            "Fiber, total dietary": "Fiber",
            "Sugars, total including NLEA": "Sugars",
            "Energy": "Calories",
            "Calcium, Ca": "Calcium",
            "Iron, Fe": "Iron",
            "Sodium, Na": "Sodium",
            "Vitamin C, total ascorbic acid": "Vitamin C"
        }

        col_width = 20
        header = f"{'Nutrient':<20}"
        for idx in range(len(self.saved_foods)):
            header += f"Food {idx + 1:<15}"
        print(header)
        print("-" * 80)

        # Print each nutrient row
        for nutrient in sorted(all_nutrient_names):
            display_name = nutrient_display_names.get(nutrient, nutrient)
            row = f"{display_name:<20}"

            for food in self.saved_foods:
                if nutrient in food['nutrients']:
                    value = food['nutrients'][nutrient]['value']
                    unit = food['nutrients'][nutrient]['unit']
                    row += f"{value:>8.2f} {unit:<7}"
                else:
                    row += f"{'N/A':<16}"

            print(row)

        print("\n" + "=" * 80)

        self.show_comparison_insights()

    def show_comparison_insights(self):
        """Figure out which food wins in different categories"""
        if len(self.saved_foods) < 2:
            return

        key_nutrients = ["Protein", "Fiber, total dietary", "Energy"]

        print("\nKey Insights:")
        print("-" * 80)

        for nutrient in key_nutrients:
            values = []
            for idx, food in enumerate(self.saved_foods):
                if nutrient in food['nutrients']:
                    values.append((idx, food['name'], food['nutrients'][nutrient]['value']))

            if values:
                # For calories, lower is better
                if nutrient == "Energy":
                    values.sort(key=lambda x: x[2])
                    winner = values[0]
                    display = "Lowest Calories"
                else:
                    values.sort(key=lambda x: x[2], reverse=True)
                    winner = values[0]
                    nutrient_display = nutrient.replace(", total dietary", "")
                    display = f"Highest {nutrient_display}"

                print(f"• {display}: {winner[1]} ({winner[2]:.2f})")

    def clear_saved_foods(self):
        # Clear out the comparison list
        self.saved_foods = []
        print("\n✓ Cleared all saved foods.")

    def show_saved_foods(self):
        if not self.saved_foods:
            print("\nNo foods saved for comparison yet.")
            return

        print(f"\nCurrently saved foods ({len(self.saved_foods)}):")
        for idx, food in enumerate(self.saved_foods, 1):
            print(f"{idx}. {food['name']}")

    def run(self):
            #  handles user input and calls appropriate functions
        print("\n" + "=" * 60)
        print(" " * 15 + "NUTRITION ANALYZER")
        print("=" * 60)
        print("\nWelcome! This app provides nutritional information for foods.")
        print("Data is per 100g serving from the USDA FoodData Central.")
        print("\nCommands:")
        print("  - Type a food name to search")
        print("  - 'compare' - Compare saved foods")
        print("  - 'saved' - View saved foods")
        print("  - 'clear' - Clear saved foods")
        print("  - 'quit' - Exit the app\n")

        while True:
            command = input("Enter command or food name: ").strip().lower()

            if command in ['quit', 'exit', 'q']:
                print("\nThank you for using Nutrition Analyzer!")
                break

            elif command == 'compare':
                self.compare_foods()

            elif command == 'saved':
                self.show_saved_foods()

            elif command == 'clear':
                self.clear_saved_foods()

            elif not command:
                print("Please enter a valid command or food name.\n")
                continue

            else:
                # User entered a food name to search
                print(f"\nSearching for '{command}'...")
                data = self.search_food(command)

                if data and "foods" in data:
                    self.display_results(command, data["foods"])

                    # Ask if they want to save it
                    save_choice = input("\nSave this food for comparison? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        self.save_food_for_comparison(command, data["foods"])
                else:
                    print("Unable to retrieve data. Please try again.\n")

            print()


def main():
    analyzer = NutritionAnalyzer()
    analyzer.run()


if __name__ == "__main__":
    main()
