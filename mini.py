import streamlit as st
import pypdf
import re
import random
import os
import pandas as pd
from collections import Counter

# --- KONFIGURACJA DLA MINI LOTTO ---
st.set_page_config(
    page_title="Mini Mini v2.0",
    page_icon="🎰",
    layout="centered"
)

# --- STYL ---
st.markdown("""
    <style>
    .stApp { background-color: #262730; color: white; }
    .big-number {
        font-size: 24px; font-weight: bold; color: white;
        background-color: #e91e63; /* Różowy dla Mini */
        border-radius: 50%;
        width: 50px; height: 50px; display: inline-flex;
        justify-content: center; align-items: center;
        margin: 5px; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
        border: 2px solid #f48fb1;
    }
    .metric-box {
        background-color: #333; padding: 10px; border-radius: 8px;
        text-align: center; border: 1px solid #444; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    draws = []
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text() or ""
            tokens = re.findall(r'\d+', text)
            i = 0
            while i < len(tokens):
                candidates = []
                offset = 0
                # Mini Lotto: 5 liczb z zakresu 1-42
                while len(candidates) < 5 and (i + offset) < len(tokens):
                    try:
                        val = int(tokens[i+offset])
                        if 1 <= val <= 42:
                            candidates.append(val)
                        else:
                            if candidates: break
                    except: break
                    offset += 1
                if len(candidates) == 5:
                    draws.append(candidates)
                    i += offset
                else:
                    i += 1
    except:
        return []
    return draws

def get_hot_numbers(draws):
    flat_data = [num for sublist in draws for num in sublist]
    counts = Counter(flat_data)
    # Wagi dla liczb 1-42
    weights = [counts.get(i, 1) for i in range(1, 43)]
    return weights

# --- SMART ALGORYTM MINI ---
def smart_generate_mini(weights):
    population = list(range(1, 43))
    
    # Próbujemy max 2000 razy znaleźć idealny zestaw
    for _ in range(2000):
        # 1. Losowanie ważone (Hot Numbers)
        stronger_weights = [w**1.5 for w in weights]
        
        candidates = set()
        while len(candidates) < 5:
            c = random.choices(population, weights=stronger_weights, k=1)[0]
            candidates.add(c)
        
        nums = sorted(list(candidates))
        
        # --- FILTRY MINI LOTTO ---
        
        # 1. Suma (Statystyczna średnia to ~107. Celujemy w 80-135)
        total_sum = sum(nums)
        if not (80 <= total_sum <= 135):
            continue 
            
        # 2. Parzystość (Unikamy 5:0 i 0:5)
        even_count = sum(1 for n in nums if n % 2 == 0)
        if even_count == 0 or even_count == 5:
            continue
            
        # 3. Niskie/Wysokie (Podział w Mini to 21. Unikamy wszystkich niskich/wysokich)
        low_count = sum(1 for n in nums if n <= 21)
        if low_count == 0 or low_count == 5:
            continue
            
        # 4. Kolejność (Max 2 liczby obok siebie, np. 5,6 jest OK, ale 5,6,7 odrzucamy)
        consecutive = 0
        max_consecutive = 0
        for i in range(len(nums)-1):
            if nums[i+1] == nums[i] + 1:
                consecutive += 1
            else:
                consecutive = 0
            max_consecutive = max(max_consecutive, consecutive)
        
        if max_consecutive >= 2: 
            continue
            
        return nums, total_sum, even_count

    # Fallback
    return nums, sum(nums), 0

# --- INTERFEJS ---
def main():
    st.title("🎰 Mini Mini v2.0")
    st.markdown("Algorytm Mini Lotto z filtrem Sumy (80-135) i Rozkładu.")
    
    FILE_NAME = "999los.pdf" # Plik z danymi Mini Lotto
    
    draws = load_data(FILE_NAME)
    
    if not draws:
        st.warning(f"⚠️ Brak pliku {FILE_NAME}. Działam na trybie losowym.")
        weights = [1] * 42
    else:
        st.success(f"Analiza bazy: {len(draws)} losowań Mini Lotto.")
        weights = get_hot_numbers(draws)

    if st.button("WYGENERUJ SMART KUPON", use_container_width=True):
        with st.spinner("Szukam idealnego rozkładu..."):
            result, s_sum, s_even = smart_generate_mini(weights)
            
        # Kule
        cols = st.columns(5)
        for i, n in enumerate(result):
            cols[i].markdown(f"<div class='big-number'>{n}</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Statystyki wyboru
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-box'>📐 Suma: <b>{s_sum}</b><br><small>(Norma: 80-135)</small></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'>⚖️ Parzyste: <b>{s_even}/5</b><br><small>(Balans)</small></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-box'>🔥 Baza<br><small>Statystyka + Filtr</small></div>", unsafe_allow_html=True)
        
        st.caption("System odrzucił kombinacje o zbyt niskim prawdopodobieństwie (skrajne sumy, ciągi liczb).")

if __name__ == "__main__":
    main()