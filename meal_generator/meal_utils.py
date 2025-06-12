from collections import defaultdict

def process_fixed_meals(
    fixed_meals_for_slot, df, max_servings_per_recipe,
    used_ids_day, used_ids_global, used_names_global,
    ingredient_usage_day, ingredient_usage_global,
    totals, meal_kcal
):
    meal_recipes = []
    for fixed_item in fixed_meals_for_slot:
        recipe_id = fixed_item.get("id")
        servings = fixed_item.get("servings", 1)
        fixed_row = df[df["id"] == recipe_id]
        if not fixed_row.empty:
            row = fixed_row.iloc[0]
            main_ingredient = row["main_ingredient"]
            name = row["name"]
            kcal = float(row["energy_kcal"])
            servings = min(int(servings), max_servings_per_recipe)
            total_kcal = servings * kcal
            carbs = row.get("carbs", 0)
            fats = row.get("fat", 0)
            protein = row.get("protein", 0)

            meal_recipes.append({
                "recipeId": int(row["id"]),
                "name": name,
                "mainIngredient": main_ingredient,
                "servings": round(servings, 2),
                "nutrition": {
                    "calories": round(total_kcal, 2),
                    "carbs": round(carbs * servings, 2),
                    "protein": round(protein * servings, 2),
                    "fats": round(fats * servings, 2)
                }
            })

            meal_kcal += total_kcal
            totals["calories"] += total_kcal
            totals["carbs"] += carbs * servings
            totals["protein"] += protein * servings
            totals["fats"] += fats * servings

            used_ids_day.add(int(row["id"]))
            used_ids_global.add(int(row["id"]))
            used_names_global.add(name)
            ingredient_usage_day[main_ingredient] += 1
            ingredient_usage_global[main_ingredient] += 1

    return meal_recipes, meal_kcal, totals
