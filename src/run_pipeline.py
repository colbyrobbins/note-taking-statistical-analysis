"""This script runs the whole analysis in order, from the app export to the figures.

    python src/run_pipeline.py

Steps: power analysis -> ingest -> clean -> paired t-test -> secondary analyses -> figures.
"""
import clean_data
import ingest_app_data
import make_figures
import paired_ttest
import power_analysis
import secondary_analysis


def main():
    # First we work out how many participants we needed
    print("== Power analysis")
    power_analysis.main([])

    # Then we turn the app export into tables and score every answer
    print("\n== Ingesting the app export")
    ingest_app_data.main([])
    print("\n== Scoring and clean tables")
    clean_data.main([])

    # Next we run the main test and the secondary analyses
    print("\n== Paired t-test")
    paired_ttest.main([])
    print("\n== Secondary analyses")
    secondary_analysis.main([])

    # Finally we draw the figures
    print("\n== Figures")
    make_figures.main([])


if __name__ == "__main__":
    main()
