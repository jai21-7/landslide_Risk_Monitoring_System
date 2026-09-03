"""Step 2 in the learning path: create the practice dataset."""

from ner_landslide.data import generate_history, save_history

if __name__ == "__main__":
    df = generate_history()
    path = save_history(df)
    print(f"Wrote {len(df)} rows to {path}")
    print(df.head().to_string(index=False))
    print("\nLandslide days:", int(df["landslide_occurred"].sum()), "of", len(df))
