"""Обучение и оценка классификатора на всех 9 жестах (одноканальная EMG).

Признаки и окна те же, что в train.py. Разбиение на train/test идёт по записям
(GroupShuffleSplit), чтобы окна одной записи не попадали одновременно в обе выборки.
Запуск:  python train_multiclass.py [папка_с_csv]   (по умолчанию data/gestures)
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "data/gestures"
GESTURES = {
    "rest": "Покой",
    "wrist_forward2": "Сгибание кисти",
    "wrist_back2": "Разгибание кисти",
    "fist": "Кулак",
    "razvedenie": "Разведение пальцев",
    "ukazarelny": "Сгибание указательного",
    "sredni": "Сгибание среднего",
    "beziman": "Сгибание безымянного",
    "shepot": "Щепоть",
}
WINDOW, STEP = 25, 10


def features(env, out):
    return [env.mean(), env.std(), env.max(), env.min(), np.sqrt(np.mean(env ** 2)),
            np.abs(env).sum(), out.mean(), out.std(), out.max(), out.sum(),
            np.count_nonzero(out)]


X, y, groups = [], [], []
for g in GESTURES:
    for f in sorted(glob.glob(os.path.join(DATA_DIR, f"{g}_[0-9]*.csv"))):
        df = pd.read_csv(f)
        env, out = df["envelope"].values, df["output"].values
        for s in range(0, len(env) - WINDOW, STEP):
            e, o = env[s:s + WINDOW], out[s:s + WINDOW]
            if g == "rest" or o.max() > 0:
                X.append(features(e, o)); y.append(g); groups.append(f)

X, y, groups = np.array(X), np.array(y), np.array(groups)
print(f"Окон: {len(X)}, записей: {len(set(groups))}")

tr, te = next(GroupShuffleSplit(test_size=0.2, random_state=42).split(X, y, groups))
clf = RandomForestClassifier(n_estimators=150, random_state=42).fit(X[tr], y[tr])
pred = clf.predict(X[te])
labels = [g for g in GESTURES if g in set(y[te])]
print(classification_report(y[te], pred, labels=labels,
                            target_names=[GESTURES[l] for l in labels], zero_division=0))
print(confusion_matrix(y[te], pred, labels=labels))
