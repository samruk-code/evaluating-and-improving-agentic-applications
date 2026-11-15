<!-- Task 2 — Prepare and split the dataset -->
Derive the correctness label and split the dataset. Be concise: write and run the script, print a short summary, don't explain unless something fails.

Write split_dataset.py:
- Load labeled_dataframe.csv (it already has "category" and "policy" columns from Task 1).
- Derive "correctness": "correct" if category == "pass", else "incorrect".
- Print value_counts() of "policy" (already a column, not derived here).
- Use sklearn.model_selection.train_test_split(test_size=15, random_state=42, stratify=labeled["policy"]) to split into train_df/test_df (25 train / 15 test when the labeled file has 40 rows).
- Save train_df to train_df.csv and test_df to test_df.csv (both index=False).
- Print train/test row counts and the test set's "policy" value_counts().
- Build a combined dataframe for viewing: train_df and test_df each with a "split" column set to "train"/"test", concatenated with pd.concat(..., ignore_index=True). Call save_view(combined, title="Task 2 — Train/test split", subtitle=f"{len(train_df)} train, {len(test_df)} test", name="task2-split") from df_view.
- When done, print exactly: Dataset split — N train / M test (stratified on policy). (with N and M filled in)
