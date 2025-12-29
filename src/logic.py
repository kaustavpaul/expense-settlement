import pandas as pd
from collections import defaultdict
import streamlit as st
from .utils import create_empty_dataframe

def get_participant_data(row, max_participants):
    """
    Extract participant data from a DataFrame row.
    Handles both list-based 'Participants' (from Grid) and 'Participant N' columns (from Form).
    """
    total_heads = 0
    involved_participants = []
    
    # 1. Check for list-based participants (Grid Entry)
    if 'Participants' in row and isinstance(row['Participants'], list):
        for p in row['Participants']:
            if p and isinstance(p, str):
                total_heads += 1
                # Check if this participant is already added (e.g. mixed mode) - though usually exclusive
                # For simplicity in mixed mode, we add them. Logic downstream aggregates balances.
                # However, to avoid double counting if someone uses BOTH on one row (unlikely but possible),
                # we should probably treat them distinctly.
                involved_participants.append((p.strip(), 1))

    # 2. Check for detailed columns (Form Entry)
    for i in range(1, max_participants + 1):
        name_col = f'Participant {i} Name'
        count_col = f'Participant {i} Members'
        
        if name_col in row and pd.notna(row[name_col]) and str(row[name_col]).strip():
            participant = str(row[name_col]).strip()
            count = int(row.get(count_col, 1))
            total_heads += count
            involved_participants.append((participant, count))
    
    return total_heads, involved_participants

def calculate_settlement(expenses_df):
    """
    Calculates the settlement plan based on the expenses DataFrame.
    """
    # Return early if there's nothing to calculate
    if expenses_df.empty or 'Amount' not in expenses_df or expenses_df['Amount'].sum() == 0:
        return "Enter some expenses to calculate a settlement."

    # Calculate balances
    balances = defaultdict(float)
    
    # Get all involved people
    involved_people = set()
    if 'Payer' in expenses_df:
        involved_people.update(expenses_df['Payer'].dropna())
    
    if 'Participants' in expenses_df.columns:
         for item in expenses_df['Participants']:
             if isinstance(item, list):
                 involved_people.update(item)

    participant_cols = [col for col in expenses_df.columns if 'Name' in col]
    for col in participant_cols:
        involved_people.update(expenses_df[col].dropna())

    # Initialize balances
    for person in involved_people:
        balances[person] = 0.0

    # Process each expense
    # Heuristic for max_participants based on columns
    max_participants = (len(expenses_df.columns) - 3) // 2
    
    for index, row in expenses_df.iterrows():
        try:
            payer = str(row['Payer']).strip()
            amount = float(row['Amount'])

            if pd.isna(payer) or amount <= 0:
                continue

            total_heads, involved_participants = get_participant_data(row, max_participants)

            if total_heads > 0:
                cost_per_head = amount / total_heads
                balances[payer] += amount
                for participant, count in involved_participants:
                    balances[participant] -= cost_per_head * count

        except (ValueError, TypeError):
            # In a real app, logging or warning could go here, but avoiding UI calls in logic is better
            continue

    # Generate settlement plan
    owes = sorted([(p, b) for p, b in balances.items() if b < -0.01], key=lambda x: x[1])
    gets = sorted([(p, b) for p, b in balances.items() if b > 0.01], key=lambda x: -x[1])
    
    settlements = []
    i, j = 0, 0
    while i < len(owes) and j < len(gets):
        owe_p, owe_amt = owes[i]
        get_p, get_amt = gets[j]
        settle_amt = min(abs(owe_amt), get_amt)

        settlements.append(f"{owe_p} pays {get_p}: ${settle_amt:.2f}")

        owes[i] = (owe_p, owe_amt + settle_amt)
        gets[j] = (get_p, get_amt - settle_amt)

        if abs(owes[i][1]) < 0.01: i += 1
        if abs(gets[j][1]) < 0.01: j += 1

    return "\n".join(settlements) if settlements else "Everyone is settled up!"

def generate_summary(df, all_people, num_participants):
    """Generates a financial summary DataFrame."""
    if df.empty or not all_people:
        return pd.DataFrame(index=["Total Paid", "Total Owed", "Difference"], 
                          columns=all_people).fillna(0.0)

    # Initialize totals
    total_paid = {p: 0.0 for p in all_people}
    total_owed = {p: 0.0 for p in all_people}

    # Calculate total paid
    if 'Payer' in df:
        paid_summary = df.groupby('Payer')['Amount'].sum()
        for person, amount in paid_summary.items():
            if person in total_paid:
                total_paid[person] = amount

    # Calculate total owed
    for _, row in df.iterrows():
        try:
            amount = float(row.get('Amount', 0))
            if pd.isna(amount) or amount <= 0:
                continue

            total_heads, involved_participants = get_participant_data(row, num_participants)

            if total_heads > 0:
                cost_per_head = amount / total_heads
                for participant, count in involved_participants:
                    if participant in total_owed:
                        total_owed[participant] += cost_per_head * count
        except (ValueError, TypeError):
            continue

    # Create summary DataFrame
    summary_df = pd.DataFrame([total_paid, total_owed], 
                            index=['Total Paid', 'Total Owed']).reindex(all_people, axis=1).fillna(0)
    summary_df.loc['Difference'] = summary_df.loc['Total Paid'] - summary_df.loc['Total Owed']
    
    return summary_df
