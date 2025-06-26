# Decision Matrix Comparator

A Streamlit app to help you make better decisions by comparing multiple choices against various criteria.

## Features

- **Dynamic Input**: Add and remove choices and criteria on the fly
- **Matrix Interface**: Visual matrix layout for easy comparison
- **Grading System**: Rate each choice-criteria combination on a 1-10 scale
- **Notes Support**: Add detailed text notes for each evaluation
- **Pivot View**: Toggle between different matrix orientations
- **Analysis Results**: Automatic scoring and ranking of choices
- **Persistent Data**: Your data persists during the session

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and navigate to the provided URL (usually `http://localhost:8501`)

3. Use the sidebar to:
   - Add choices (the options you're comparing)
   - Add criteria (the factors you're evaluating)
   - Toggle between normal and pivoted views
   - Clear all data when needed

4. Fill in the decision matrix:
   - Rate each choice-criteria combination (1-10 scale)
   - Add detailed notes for your reasoning
   - View automatic rankings and analysis

## Example Use Cases

- **Product Comparison**: Compare different products based on price, quality, features, etc.
- **Job Selection**: Evaluate job offers based on salary, location, benefits, growth potential
- **Investment Decisions**: Compare investment options based on risk, return, liquidity
- **Travel Planning**: Choose destinations based on cost, weather, activities, accessibility

## How It Works

The app creates a decision matrix where:
- **X-axis**: Criteria (factors to evaluate)
- **Y-axis**: Choices (options being compared)
- **Cells**: Grades (1-10) and notes for each combination

The app automatically calculates:
- Total scores for each choice
- Average scores
- Rankings with medals (🥇🥈🥉)

Use the pivot button to swap the axes for a different perspective on your data! 