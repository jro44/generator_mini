import streamlit as st
import pypdf
import re
import random
import os
import pandas as pd
import time
from collections import Counter
from datetime import datetime

# --- 1. KONFIGURACJA STRONY (Kasynowy Vibe) ---
st.set_page_config(
    page_title="Lotto Casino 777",
    page_icon="🎰",
    layout="centered" # Wyśrodkowany układ jak w maszynie
)

FILE_PATH = "999los.pdf"

# --- 2. STYLIZACJA (Neon, Złoto, Czerń) ---
def local_css():
    st.markdown("""
    <style>
    /* Tło - Głęboka czerń */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(145deg, #1a0b00 0%, #000000 74%);
        color: #FFD700;
    }
    
    /* Nagłówek - Neonowy styl */
    h1 {
        text-align: center;
        color: #FF0055 !important;
        text-shadow: 0 0 10px #FF0055, 0 0 20px #FF0055;
        font-family: 'Courier New', Courier, monospace;
        font-weight: 900;
        font-size: 3rem;
        letter-spacing: 5px;
    }
    
    /* Przycisk SPIN - Wygląd dźwigni */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(0deg, #cc0000 0%, #ff3333 100%);
        color: white !important;
        font-size: 24px;
        font-weight: bold;
        border: 4px solid #800000 !important;
        border-radius: 15px;
        box-shadow: 0 10px 0 #500000, 0 15px 20px rgba(0,0,0,0.5);
        transition: all 0.1s;
        text-transform: uppercase;
        margin-top: 20px;
    }
    div.stButton > button:active {
        transform: translateY(10px);
        box-shadow: 0 0 0 #500000, 0 0 0 rgba(0,0,0,0);
    }
    div.stButton > button:hover {
        background: linear-gradient(0deg, #ff0000 0%, #ff6666 100%);
    }

    /* Wyświetlacz Maszyny (Sloty) */
    .slot-container {
        display: flex;
        justify-content: center;
        background-color: #111;
        padding: 20px;
        border: 10px solid #DAA520; /* Złota ramka */
        border-radius: 20px;
        box-shadow: inset 0 0 30px #000;
        margin-bottom: 20px;
    }
    
    .slot-window {
        background-color: #fff;
        color: #000;
        width: 60px;
        height: 80px;
        line-height: 80px;
        margin: 0 5px;
        text-align: center;
        font-size: 35px;
        font-weight: bold;
        border: 3px solid #555;
        border-radius: 5px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        font-family: 'Arial Black', sans-serif;
    }
    
    /* Efekt wygranej (miganie) */
    @keyframes blinker {
        50% { opacity: 0.5; box-shadow: 0 0 20px #FFD700; }
    }
    .winner {
        border-color: #FFD700;
        color: #FF0055;
        animation: blinker 1s linear infinite;
    }
    
    .stat-box {
        background-color: #222;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #444;
        margin-top: 10px;
        font-size: 14px;
        color: #ccc;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 3. PARSER PDF ---
@st.cache_data
def load_data(path):
    if not os.path.exists(path):
        return []
    
    draws = []
    try:
        reader = pypdf.PdfReader(path)
        for page in reader.pages:
            text = page.extract_text() or ""
            tokens = re.findall(r'\d+', text)
            
            i = 0
            while i < len(tokens):
                candidates = []
                offset = 0
                # Próbujemy znaleźć ciąg 5 liczb <= 50 (dla Mini Lotto 42, dla Euro 50)
                # Zakładamy bezpiecznie max 50
                while len(candidates) < 5 and (i + offset) < len(tokens):
                    try:
                        val = int(tokens[i+offset])
                        # Filtrujemy ID losowania (zazwyczaj duże liczby)
                        if 1 <= val <= 50: 
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
    
    # Zwracamy listę losowań (najnowsze na początku lub na końcu - zakładamy kolejność z pliku)
    # Dla logiki "ostatnie 3 losowania" kolejność jest kluczowa.
    return draws

# --- 4. LOGIKA KASYNA ---
def casino_algorithm(draws):
    if not draws:
        return sorted(random.sample(range(1, 43), 5)), "Losowy (Brak danych)"

    # 1. Statystyka Częstotliwości (Globalna)
    flat_all = [n for d in draws for n in d]
    counts = Counter(flat_all)
    total_draws = len(draws)
    
    # 2. Sprawdź, kiedy liczba wystąpiła ostatnio
    # Szukamy od końca listy (zakładamy, że koniec listy to najnowsze, jeśli parser czyta w dół)
    # Dla pewności odwróćmy, żeby indeks 0 to było najnowsze losowanie
    # (Zależy od struktury PDF, ale zazwyczaj czyta od góry)
    # Przyjmijmy: Ostatnie wczytane = Najnowsze.
    
    last_seen_index = {} # liczba -> ile losowań temu (0 = było w ostatnim)
    
    # Iterujemy od tyłu (najnowsze losowania)
    reversed_draws = list(reversed(draws))
    
    for idx, draw in enumerate(reversed_draws):
        for num in draw:
            if num not in last_seen_index:
                last_seen_index[num] = idx
                
    # 3. Wybór kandydatów
    candidates_pool = []
    
    # Próg bycia "Częstym" (np. górne 50% liczb)
    avg_freq = sum(counts.values()) / len(counts)
    
    for num in range(1, 43): # Zakres Mini Lotto (lub 50 dla Euro)
        # Ile razy padła
        freq = counts.get(num, 0)
        # Ile losowań temu (jeśli nie było wcale, dajemy 999)
        ago = last_seen_index.get(num, 999)
        
        weight = freq # Podstawowa waga to częstotliwość
        
        # LOGIKA UŻYTKOWNIKA:
        # "jeżeli nie widniała ponad 3 losowania i była częsta"
        is_frequent = freq > avg_freq
        is_due = ago > 3
        
        if is_frequent and is_due:
            # Super Bonus! To jest nasz "Pewniak"
            weight *= 5 # Zwiększamy szansę 5-krotnie
            tag = "🔥" # Gorący i Śpiący
        elif is_frequent:
            weight *= 1.5 # Tylko częsty
            tag = "☀️"
        elif is_due:
            weight *= 1.2 # Tylko śpiący
            tag = "💤"
        else:
            weight *= 0.5 # Rzadki i był niedawno (zimny)
            tag = "❄️"
            
        candidates_pool.append({
            "num": num,
            "weight": weight,
            "tag": tag,
            "ago": ago
        })
    
    # 4. Losowanie ważone
    # Wybieramy 5 liczb na podstawie wag
    chosen = []
    population = [c["num"] for c in candidates_pool]
    weights = [c["weight"] for c in candidates_pool]
    
    while len(chosen) < 5:
        pick = random.choices(population, weights=weights, k=1)[0]
        if pick not in chosen:
            chosen.append(pick)
            
    chosen.sort()
    
    # Info o wybranych dla użytkownika
    info = []
    for num in chosen:
        cand = next(c for c in candidates_pool if c["num"] == num)
        info.append(cand)
        
    return chosen, info

# --- 5. INTERFEJS ---
def main():
    st.title("🎰 CASINO LOTTO 🎰")
    st.markdown("<p style='text-align: center; color: #aaa;'>ALGORYTM 'ŚPIĄCYCH GIGANTÓW'</p>", unsafe_allow_html=True)

    draws = load_data(FILE_PATH)
    if not draws:
        st.error(f"Nie znaleziono pliku {FILE_PATH}!")
        return

    # Stan maszyny
    if 'last_spin' not in st.session_state:
        st.session_state['last_spin'] = [7, 7, 7, 7, 7]
    if 'spin_info' not in st.session_state:
        st.session_state['spin_info'] = None

    # Dźwignia
    if st.button("POCIĄGNIJ DŹWIGNIĘ 🕹️"):
        with st.spinner("Bębny się kręcą..."):
            time.sleep(1.5) # Budowanie napięcia
            nums, details = casino_algorithm(draws)
            st.session_state['last_spin'] = nums
            st.session_state['spin_info'] = details

    # Wyświetlacz wyników
    nums = st.session_state['last_spin']
    
    st.markdown(f"""
    <div class="slot-container">
        <div class="slot-window">{nums[0]}</div>
        <div class="slot-window">{nums[1]}</div>
        <div class="slot-window">{nums[2]}</div>
        <div class="slot-window">{nums[3]}</div>
        <div class="slot-window">{nums[4]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sekcja Wyjaśnienia (Dlaczego te liczby?)
    if st.session_state['spin_info']:
        st.markdown("### 🕵️ ANALIZA WYGRANEJ:")
        
        cols = st.columns(5)
        for i, info in enumerate(st.session_state['spin_info']):
            with cols[i]:
                # Kolorowanie w zależności od typu
                color = "#fff"
                if info['tag'] == "🔥": color = "#FF0055" # Super
                elif info['tag'] == "☀️": color = "#FFD700" # Częsty
                
                st.markdown(f"""
                <div class="stat-box" style="border-color: {color};">
                    <div style="font-size: 20px; font-weight: bold; color: {color}; text-align: center;">{info['num']}</div>
                    <hr style="margin: 5px 0; border-color: #444;">
                    Typ: {info['tag']}<br>
                    Ostatnio: {info['ago']} los.<br>
                </div>
                """, unsafe_allow_html=True)
                
        st.caption("""
        🔥 **Ogień:** Liczba częsta, która "śpi" (nie było jej >3 losowania). System ją wybrał!
        ☀️ **Słońce:** Bardzo częsta liczba.
        💤 **Sen:** Liczba rzadka, ale dawno niewylosowana.
        """)
        
        # Zapisz wynik
        if st.button("💾 ZAPISZ KUPON"):
            with open("Kupon_Casino.txt", "a") as f:
                f.write(f"CASINO SPIN: {nums} | Data: {datetime.now()}\n")
            st.success("Zapisano!")

if __name__ == "__main__":
    main()