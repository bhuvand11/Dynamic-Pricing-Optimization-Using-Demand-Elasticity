# Dynamic Pricing Optimization Using Demand Elasticity

![Python](https://img.shields.io/badge/Python-3.11.8-blue)
![ML](https://img.shields.io/badge/Machine%20Learning-Retail%20Analytics-green)

##  Project Overview

An end-to-end machine learning project that develops a data-driven dynamic pricing optimization system for the retail sector using Walmart Sales data. The system predicts product demand under varying conditions and identifies optimal prices that maximize revenue.

##  Objectives

- **Predict demand** using machine learning regression models
- **Analyze price elasticity** to understand demand sensitivity to price changes
- **Optimize revenue** by recommending optimal pricing strategies
- **Provide actionable insights** through comprehensive visualizations

##  Dataset

**Walmart Sales Dataset** - Historical weekly sales data from 45 Walmart stores

**Features:**
- `Store` - Store ID (1-45)
- `Date` - Weekly timeline (Feb 2010 - 2011)
- `Weekly_Sales` - Target variable (sales in dollars)
- `Holiday_Flag` - Binary holiday indicator
- `Temperature` - Weekly temperature
- `Fuel_Price` - Fuel price per gallon
- `CPI` - Consumer Price Index
- `Unemployment` - Unemployment rate

**Dataset Size:** 6,435 records

## Project Structure

```
Dynamic-Pricing-Optimization-Using-Demand-Elasticity/
│
├── data/
│   ├── Walmart.csv                    # Original dataset
│   ├── walmart_processed.csv          # Processed dataset with features
│   └── walmart_model_ready.csv        # Clean dataset ready for modeling
│
├── notebooks/
│   ├── 01_data_exploration_and_preprocessing.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_demand_prediction_models.ipynb
│   ├── 04_price_elasticity_analysis.ipynb
│   └── 05_revenue_optimization.ipynb
│
├── src/
│   ├── data_processing.py
│   ├── model_training.py
│   ├── price_optimizer.py
│   └── visualization.py
│
├── models/
│   └── trained_models/                # Saved ML models
│
├── output/
│   ├── figures/                       # Generated plots and visualizations
│   └── results/                       # Analysis results and reports
│
├── requirements.txt                   # Python dependencies
├── instructions.txt                   # Project requirements document
└── README.md                          # Project documentation
```

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Dynamic-Pricing-Optimization-Using-Demand-Elasticity.git
cd Dynamic-Pricing-Optimization-Using-Demand-Elasticity
```

### 2. Create Virtual Environment
```bash
python -m venv d_env
```

### 3. Activate Virtual Environment
**Windows:**
```bash
.\d_env\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source d_env/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch Jupyter Notebook
```bash
jupyter notebook
```

## Project Methodology

### Phase 1: Data Exploration and Preprocessing 
- Load and inspect dataset
- Handle missing values and outliers
- Exploratory data analysis (EDA)
- Statistical analysis and visualization
- Data cleaning

### Phase 2: Feature Engineering
- Extract temporal features (year, month, season, week)
- Create lag features and rolling statistics
- **Simulate price variables** for elasticity analysis
- Encode categorical variables
- Feature scaling and normalization

### Phase 3: Demand Prediction Models
- Train multiple regression models:
  - Linear Regression (baseline)
  - Random Forest Regressor
  - Gradient Boosting Regressor
- Model evaluation (MAE, RMSE, R²)
- Feature importance analysis
- Cross-validation
- Select best performing model

### Phase 4: Price Elasticity Analysis
- Simulate price variations
- Calculate demand elasticity coefficients
- Analyze price sensitivity across:
  - Different stores
  - Seasonal periods
  - Holiday vs non-holiday weeks

### Phase 5: Revenue Optimization
- Build optimization framework
- Calculate: **Revenue = Price × Predicted Demand**
- Identify optimal price points for maximum revenue
- Create dynamic pricing recommendations
- Scenario analysis

### Phase 6: Visualization & Insights
- Demand trends over time
- Price vs demand curves
- Revenue optimization charts
- Feature importance visualizations
- Business intelligence dashboard

## 🛠️ Technologies & Tools

- **Python 3.11.8** - Core programming language
- **Pandas & NumPy** - Data processing and numerical computing
- **Matplotlib & Seaborn** - Data visualization
- **Scikit-learn** - Machine learning models
- **Jupyter Notebook** - Interactive development environment

## 📈 Key Metrics

- **Mean Absolute Error (MAE)** - Average prediction error
- **Root Mean Squared Error (RMSE)** - Penalizes large errors
- **R² Score** - Model fit quality
- **Price Elasticity** - Demand responsiveness to price changes
- **Revenue Optimization** - Profit maximization metrics

## 🎓 Learning Outcomes

This project demonstrates:
- End-to-end machine learning pipeline development
- Real-world business problem solving
- Regression modeling and ensemble methods
- Feature engineering techniques
- Economic modeling (price elasticity)
- Revenue optimization strategies
- Data visualization and storytelling

## Dependencies

See [requirements.txt](requirements.txt) for complete list:
- pandas==2.1.4
- numpy==1.26.2
- matplotlib==3.8.2
- seaborn==0.13.0
- scikit-learn==1.3.2
- jupyter==1.0.0
- notebook==7.0.6
- ipykernel==6.27.1

##  Usage

1. Start with `01_data_exploration_and_preprocessing.ipynb` for data understanding
2. Progress through numbered notebooks sequentially
3. Run all cells in each notebook to reproduce results
4. Visualizations are automatically saved to `output/` directory
5. Trained models are saved to `models/` directory

##  Expected Results

- **Demand Prediction Model** with high accuracy (low MAE/RMSE)
- **Price Elasticity Insights** for each store and time period
- **Optimal Pricing Recommendations** to maximize revenue
- **Interactive Visualizations** for business decision-making
- **Complete Analysis Report** with actionable insights

## Contributors

- Team Member 1 - Data Engineering & Pipeline
- Team Member 2 - ML Model Development
- Team Member 3 - Business Analytics & Optimization
- Team Member 4 - Visualization & Documentation

##  License

This project is for educational purposes.

## Acknowledgments

- Walmart Sales Dataset
- VS Code with GitHub Copilot for assisted development

---

**Project Status:** In Progress - Phase 1 Complete

*Last Updated: March 2026*
