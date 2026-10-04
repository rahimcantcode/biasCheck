"""Each sentence gets one vote in the article summary."""
LABELS = ('LEFT', 'CENTER', 'RIGHT')

def summarize_predictions(predictions):
    counts = {label: 0 for label in LABELS}
    for prediction in predictions:
        counts[prediction['label']] += 1
    total = sum(counts.values())
    winners = [label for label, count in counts.items() if count == max(counts.values())]
    return {
        'total_sentences': total,
        'counts': counts,
        'shares': {label: count / total if total else 0.0 for label, count in counts.items()},
        'label': winners[0] if total and len(winners) == 1 else None,
        'method': 'sentence_vote',
    }
