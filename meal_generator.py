from collections import defaultdict

MEAL_TYPES = {
    0: "breakfast",
    1: "midMorningSnack",
    2: "lunch",
    3: "afternoonSnack",
    4: "dinner"
}

DAY_NAMES = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

MEAL_SPLIT = {
    0: 0.20,
    1: 0.10,
    2: 0.35,
    3: 0.10,
    4: 0.25
}

def generate_api_meal_plan(df, target_kcal, carbs_ratio, fat_ratio, protein_ratio, nb_days, fixed_meals=None):
    if fixed_meals is None:
        fixed_meals = {}

    meal_plan = []
    ingredient_limit = 2
    max_servings_per_recipe = 3 if target_kcal >= 2000 else 2

    used_ids_global = set()
    ingredient_usage_global = defaultdict(int)
    used_names_global = set()

    for i in range(nb_days):
        day_name = DAY_NAMES[i]
        used_ids_day = set()
        ingredient_usage_day = defaultdict(int)
        day_plan = {"day": day_name, "mealTypes": {}, "dailyTotals": {}}
        totals = {"calories": 0, "carbs": 0, "protein": 0, "fats": 0}

        for cat_id, meal_key in MEAL_TYPES.items():
            meal_target = target_kcal * MEAL_SPLIT[cat_id]
            meal_tolerance = 0.15 * meal_target
            min_kcal, max_kcal = meal_target - meal_tolerance, meal_target + meal_tolerance

            meal_recipes = []
            meal_kcal = 0

            fixed_meals_for_slot = fixed_meals.get(day_name, {}).get(meal_key, [])
            if isinstance(fixed_meals_for_slot, dict):
                fixed_meals_for_slot = [fixed_meals_for_slot]

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

            # Complément automatique si nécessaire
            valid = df[df["categories"].str.contains(str(cat_id))].copy()
            valid = valid[
                ~valid["id"].isin(used_ids_day) &
                ~valid["id"].isin(used_ids_global) &
                ~valid["name"].isin(used_names_global)
            ].sample(frac=1)

            for _, row in valid.iterrows():
                main_ingredient = row["main_ingredient"]
                name = row["name"]

                if ingredient_usage_day[main_ingredient] >= ingredient_limit:
                    continue
                if ingredient_usage_global[main_ingredient] >= ingredient_limit:
                    continue

                kcal = float(row["energy_kcal"])
                max_serv = int((max_kcal - meal_kcal) // kcal)
                if max_serv <= 0:
                    continue

                servings = min(int(row["servings"]), max_serv, max_servings_per_recipe)
                if servings <= 0:
                    continue

                total_kcal = servings * kcal
                if meal_kcal + total_kcal > max_kcal:
                    continue

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

                if meal_kcal >= min_kcal:
                    break

            day_plan["mealTypes"][meal_key] = meal_recipes

        day_plan["dailyTotals"] = {
            "calories": round(totals["calories"], 2),
            "carbs": round(totals["carbs"], 2),
            "protein": round(totals["protein"], 2),
            "fats": round(totals["fats"], 2),
            "calorieDeviation": round(abs(totals["calories"] - target_kcal), 2)
        }

        meal_plan.append(day_plan)

    return {
        "success": True,
        "mealPlan": meal_plan,
        "targets": {
            "caloriesPerDay": round(target_kcal, 2),
            "carbs": round((target_kcal * carbs_ratio), 2),
            "protein": round((target_kcal * protein_ratio), 2),
            "fats": round((target_kcal * fat_ratio), 2)
        }
    }
