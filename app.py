from flask import Flask, request, send_file, jsonify
import json, os

from meal_generator.generator import generate_api_meal_plan
from data_loader import load_recipe_data

app = Flask(__name__)

df = load_recipe_data("data/recipe_api.csv")

@app.route("/api/generate-meal-plan", methods=["POST"])
def api_generate_meal_plan_route():
    try:
        data = request.get_json()
        kcal = data["calories"]
        carbs = data["carbs"]
        fats = data["fats"]
        protein = data["protein"]
        days = int(data["days"])
        fixed_meals_raw = data.get("fixed_meals", {})

        # 🔁 Normaliser tous les formats possibles de fixed_meals
        fixed_meals = {}
        for day, meals in fixed_meals_raw.items():
            day_upper = day.upper()
            fixed_meals[day_upper] = {}
            for meal_type, recipe_data in meals.items():
                if isinstance(recipe_data, dict):
                    fixed_meals[day_upper][meal_type] = [recipe_data]
                elif isinstance(recipe_data, list):
                    fixed_meals[day_upper][meal_type] = recipe_data
                else:
                    fixed_meals[day_upper][meal_type] = [{"id": recipe_data, "servings": 1}]

        result = generate_api_meal_plan(
            df,
            target_kcal=kcal,
            carbs_ratio=carbs,
            fat_ratio=fats,
            protein_ratio=protein,
            nb_days=days,
            fixed_meals=fixed_meals
        )

        os.makedirs("output", exist_ok=True)
        with open("output/last_week_plan.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/plan", methods=["GET"])
def serve_json():
    path = "output/last_week_plan.json"
    if os.path.exists(path):
        return send_file(path, as_attachment=False)
    return "Aucun JSON généré", 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
