.PHONY: install generate api pipeline dashboard test all clean

# Install all dependencies
install:
	pip install -r requirements.txt

# Generate synthetic hospital data
generate:
	python -m scripts.generate_synthetic_data

# Start the FastAPI server (source simulator + serving API)
api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run the ETL pipeline
pipeline:
	python -m src.hospital_pipeline.pipeline

# Launch the Streamlit dashboard
dashboard:
	streamlit run app/streamlit_app.py

# Run all tests (uses SQLite, no MySQL needed)
test:
	pytest tests/ -v

# Full workflow: generate data -> start API -> run pipeline
all: generate pipeline

# Remove generated data and logs
clean:
	rm -rf data/raw/*.csv data/raw/*.json data/staging/*.csv data/staging/*.json logs/
