import serial
import csv
import time
import glob
import os

PORT = 'COM3'
BAUD = 115200

DURATION = 3  # секунд записи

#LABEL = 'wrist_back2'
#LABEL = 'wrist_forward2'
LABEL = 'rest'

label_base = LABEL  # базовое имя для поиска и меток

# ищем существующие файлы этого типа
DATA_DIR = 'data/gestures'
existing = glob.glob(f'{DATA_DIR}/{label_base}_*.csv')

max_idx = 0
for fname in existing:
    base = os.path.basename(fname)
    name = base.replace('.csv', '')
    parts = name.split('_')
    if len(parts) >= 2 and parts[-1].isdigit():
        idx = int(parts[-1])
        if idx > max_idx:
            max_idx = idx

new_idx = max_idx + 1
filename = f'{DATA_DIR}/{label_base}_{new_idx:02d}.csv'
label_full = f'{label_base}_{new_idx:02d}'

print(f"Будем записывать в файл: {filename}")
print(f"Метка внутри файла: {label_full}")

ser = serial.Serial(PORT, BAUD)
time.sleep(2)

with open(filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['time', 'envelope', 'output', 'label'])
    start = time.time()
    while time.time() - start < DURATION:
        line = ser.readline().decode(errors='ignore').strip()
        try:
            envelope, output = line.split(',')
            writer.writerow([
                time.time(),
                float(envelope),
                float(output),
                label_full
            ])
            print(envelope, output)
        except:
            pass

print('DONE')
ser.close()