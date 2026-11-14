import glob
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import joblib

# соберём все записи
files = []
files += glob.glob('data/gestures/wrist_forward2_*.csv')
files += glob.glob('data/gestures/wrist_back2_*.csv')
files += glob.glob('data/gestures/rest_*.csv')

print("Найдено файлов:", files)

all_data = []
for file in files:
    df = pd.read_csv(file)
    all_data.append(df)

full_df = pd.concat(all_data, ignore_index=True)
print("Исходные метки:")
print(full_df['label'].value_counts())

def normalize_label(raw_label):
    if isinstance(raw_label, str):
        if raw_label.startswith('wrist_forward2'):
            return 'wrist_forward2'
        elif raw_label.startswith('wrist_back2'):
            return 'wrist_back2'
        elif raw_label.startswith('rest'):
            return 'rest'
    return raw_label

full_df['label'] = full_df['label'].apply(normalize_label)
print("После нормализации:")
print(full_df['label'].value_counts())

window_size = 25
step = 10

X = []
y = []

def features_from_window(env, out):
    return [
        np.mean(env),
        np.std(env),
        np.max(env),
        np.min(env),
        np.sqrt(np.mean(env ** 2)),
        np.sum(np.abs(env)),
        np.mean(out),
        np.std(out),
        np.max(out),
        np.sum(out),
        np.count_nonzero(out),
    ]

for label in full_df['label'].unique():
    df_label = full_df[full_df['label'] == label]
    env_signal = df_label['envelope'].values
    out_signal = df_label['output'].values

    for start in range(0, len(env_signal) - window_size, step):
        env_window = env_signal[start:start + window_size]
        out_window = out_signal[start:start + window_size]

        if label == 'rest':
            X.append(features_from_window(env_window, out_window))
            y.append(label)
        else:
            if np.max(out_window) > 0:
                X.append(features_from_window(env_window, out_window))
                y.append(label)

X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

clf = RandomForestClassifier(
    n_estimators=150,
    random_state=42
)

clf.fit(X_train, y_train)
predictions = clf.predict(X_test)

print('\n=== CLASSIFICATION REPORT ===')
print(classification_report(y_test, predictions))

print('\n=== CONFUSION MATRIX ===')
print(confusion_matrix(y_test, predictions))

for label in full_df['label'].unique():
    signal = full_df[full_df['label'] == label]['envelope'].values
    plt.figure(figsize=(12, 4))
    plt.plot(signal)
    plt.title(label)
    plt.xlabel('Sample')
    plt.ylabel('Envelope')
    plt.show()

joblib.dump(clf, 'emg_model.pkl')
print('MODEL SAVED: emg_model.pkl')