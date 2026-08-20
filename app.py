import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import io

# Ayarlar
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.1-flash-lite') # Limit sorunu yaşamamak için stabil model

st.set_page_config(page_title="MeLingo Akademik Asistan", layout="wide")
st.title("🎓 MeLingo - Akademik İngilizce Platformu")

# --- VERİ VE SESSION STATE ---
if "used_topics" not in st.session_state: st.session_state.used_topics = []
if "current_topic" not in st.session_state: st.session_state.current_topic = ""

# Geçici kitap listesi
kitap_listesi = {
    "Student's Book": "Akademik okuma parçaları ve dil bilgisi içerir.",
    "Workbook": "Alıştırma odaklı içerikler.",
    "Essay Kurallari": "Giriş, gelişme, sonuç. Formal dil kullanımı. Kelime sayısı 250+."
}

# Sidebar
st.sidebar.header("📚 Kütüphane")
secilen_kitap = st.sidebar.selectbox("Kaynak:", list(kitap_listesi.keys()))
kitap_metni = kitap_listesi.get(secilen_kitap, "")

# --- MODÜLLER ---
# 6 sekmeyi de tanımlıyoruz
tab1, tab2, tab3, tab4, tab5, tab6= st.tabs(["Günün Kelimesi", "Boşluk Doldurma", "Okuma", "Dinleme", "Essay Yazımı", "Test"])

with tab1:
    st.header("Günün Kelimesi")
    if st.button("Kelime Üret"):
        st.markdown(model.generate_content(f"Seçilen kitap: {secilen_kitap}. Bu kitaba uygun, B2 seviyesinde akademik bir kelime seç ve örnek cümle kur.").text)

with tab2:
    st.header("Boşluk Doldurma")
    st.write("Sistem kitaptan 10 cümle seçti. Aşağıdaki kelimeleri uygun boşluklara yerleştir bakalım!")

    if "quiz_questions" not in st.session_state: st.session_state.quiz_questions = None
    if "quiz_answers_hidden" not in st.session_state: st.session_state.quiz_answers_hidden = None
    if "word_bank" not in st.session_state: st.session_state.word_bank = None

    if st.button("10 Soru Hazırla"):
        with st.spinner("Kitabını tarıyorum, özel 10 soru hazırlıyorum..."):
            prompt = f"""
            Seçilen kitap metni: {kitap_metni[:15000]}
            
            ÖNEMLİ KURAL: Hazırlayacağın tüm cümleler ve kelimeler KESİNLİKLE yukarıdaki İngilizce metinden alınmalı ve orijinal İNGİLİZCE dilinde olmalıdır. Kesinlikle Türkçe çeviri yapma!
            
            Bu metinden, akademik değeri olan cümleleri seçerek 10 adet boşluk doldurma sorusu hazırla.
            Her İngilizce cümlenin boşluk olan yerine '___' koy.
            
            Lütfen çıktıyı KESİNLİKLE şu formatta ver (araya '|||' koymayı unutma, tam 3 parça olmalı):
            
            [Sadece İngilizce Sorular - 1'den 10'a kadar numaralandırılmış]
            |||
            [Sadece İngilizce Cevap Kelimeleri - Sadece virgülle ayrılmış 10 adet İngilizce kelime yaz, başka hiçbir açıklama yapma]
            |||
            [Cevap Anahtarı - 1'den 10'a kadar İngilizce cevaplar]
            """
            
            cevap = model.generate_content(prompt).text
            
            try:
                import random # Kelimeleri karıştırmak için
                
                # Gelen cevabı 3 parçaya bölüyoruz
                sorular, kelimeler_str, cevaplar = cevap.split("|||")
                
                # Kelimeleri listeye çevir, sağındaki solundaki boşlukları temizle ve KARIŞTIR
                kelimeler_listesi = [k.strip() for k in kelimeler_str.split(",")]
                random.shuffle(kelimeler_listesi) # İşte burada sırasını tamamen rastgele yapıyoruz!
                
                st.session_state.word_bank = " • ".join(kelimeler_listesi) # Araya şık bir nokta koyarak birleştiriyoruz
                st.session_state.quiz_questions = sorular.strip()
                st.session_state.quiz_answers_hidden = cevaplar.strip()
                st.rerun() 
            except Exception as e:
                st.error("Soruları hazırlarken ufak bir karışıklık oldu, lütfen tekrar bas aşkım.")

    if st.session_state.quiz_questions:
        # Karışık kelime havuzunu ekranda şık, mavi bir kutu içinde gösteriyoruz
        st.info(f"**Kullanılacak Kelimeler:**\n\n {st.session_state.word_bank}")
        
        st.markdown(st.session_state.quiz_questions)
        
        st.subheader("Cevaplarını Buraya Yaz")
        user_answers = st.text_area("Cevaplarını sırasıyla virgülle ayırarak yaz (Örn: kelime1, kelime2, ...):", height=100)
        
        if st.button("Kontrol Et (Melek Modu)"):
            with st.spinner("Kontrol ediyorum aşkım..."):
                prompt = f"""
                Sen Melek'sin. Uğur'un boşluk doldurma cevaplarını kontrol ediyorsun.
                Sorular: {st.session_state.quiz_questions}
                Gerçek Cevaplar: {st.session_state.quiz_answers_hidden}
                Uğur'un cevapları: {user_answers}
                
                Uğur'a tatlı bir dille geri bildirim ver. Kaç doğrusu var söyle. 
                Yanlışları varsa neden yanlış olduğunu açıkla ve motive et.
                """
                st.markdown(model.generate_content(prompt).text)

with tab3:
    st.header("Okuma")
    st.write("Uzun ve detaylı bir okuma parçasının ardından seni 10 soruluk bir test bekliyor. Tüm şıkları işaretle ve kontrol et!")
    
    # Hafıza (Session State) tanımlamaları
    if "reading_passage" not in st.session_state: st.session_state.reading_passage = ""
    if "reading_questions" not in st.session_state: st.session_state.reading_questions = []
    if "reading_submitted" not in st.session_state: st.session_state.reading_submitted = False

    if st.button("Parçayı ve Soruları Oluştur"):
        with st.spinner("Kitabından bir parça seçiyorum ve 10 soru hazırlıyorum..."):
            # Gemini'den uzun metin ve kesin bir format istiyoruz
            prompt = f"""
            Seçilen kitap: {secilen_kitap}.
            Bu kitaptan B2 seviyesinde, UZUN, detaylı ve akademik bir okuma parçası seç. (En az 3-4 paragraf olsun).
            Ardından bu metne dayalı TAM 10 adet çoktan seçmeli soru hazırla.
            
            Çıktıyı KESİNLİKLE aşağıdaki formata tam uyarak ver (Bölümler arasına '|||', şıklar arasına '|' koy):
            
            [OKUMA PARÇASI METNİ - Buraya tüm paragrafları yaz]
            |||
            Soru 1'in Metni | A şıkkının metni | B şıkkının metni | C şıkkının metni | D şıkkının metni | Doğru Şıkkın Harfi (Sadece A, B, C veya D)
            |||
            Soru 2'nin Metni | A şıkkının metni | B şıkkının metni | C şıkkının metni | D şıkkının metni | Doğru Şıkkın Harfi
            (Bu şekilde tam 10 soruya kadar devam et.)
            """
            
            cevap = model.generate_content(prompt).text
            
            try:
                # Gelen metni bölüp ayrıştırıyoruz
                parcalar = cevap.split("|||")
                st.session_state.reading_passage = parcalar[0].strip()
                
                soru_listesi = []
                for p in parcalar[1:]:
                    if p.strip():
                        bolumler = [b.strip() for b in p.split("|")]
                        if len(bolumler) >= 6:
                            soru_listesi.append({
                                "soru": bolumler[0],
                                "A": bolumler[1],
                                "B": bolumler[2],
                                "C": bolumler[3],
                                "D": bolumler[4],
                                "cevap": bolumler[5].upper().replace(")", "").strip()[0] # Güvenlik: Sadece harfi al
                            })
                st.session_state.reading_questions = soru_listesi
                st.session_state.reading_submitted = False # Yeni test geldi, henüz çözülmedi
                st.rerun()
            except Exception as e:
                st.error("Soruları hazırlarken metin formatında ufak bir karışıklık oldu, lütfen tekrar bas aşkım.")

    if st.session_state.reading_passage:
        st.markdown("### 📖 Okuma Parçası")
        st.info(st.session_state.reading_passage)
        
        st.markdown("### 📝 Test (10 Soru)")
        
        # EĞER TEST HENÜZ KONTROL EDİLMEDİYSE ÇÖZME EKRANINI GÖSTER
        if not st.session_state.reading_submitted:
            with st.form("reading_quiz_form"):
                for i, q_data in enumerate(st.session_state.reading_questions):
                    secenekler = [f"A) {q_data['A']}", f"B) {q_data['B']}", f"C) {q_data['C']}", f"D) {q_data['D']}"]
                    st.radio(f"**{i+1}. {q_data['soru']}**", secenekler, key=f"read_q_{i}", index=None)
                
                submit_btn = st.form_submit_button("Hadi Kontrol Edelim!")
                
                if submit_btn:
                    st.session_state.reading_submitted = True
                    st.rerun()
                    
        # EĞER TEST KONTROL EDİLDİYSE SONUÇ (RENKLİ) EKRANINI GÖSTER
        else:
            dogru_sayisi = 0
            sorular_ve_yanitlar_str = "" # Gemini'ye göndermek için kayıt tutuyoruz
            
            for i, q_data in enumerate(st.session_state.reading_questions):
                user_ans_full = st.session_state.get(f"read_q_{i}")
                user_ans_letter = user_ans_full[0] if user_ans_full else None
                correct_letter = q_data['cevap']
                
                sorular_ve_yanitlar_str += f"Soru: {q_data['soru']} | Uğur'un Seçimi: {user_ans_letter} | Doğrusu: {correct_letter}\n"
                
                st.write(f"**{i+1}. {q_data['soru']}**")
                
                # Şıkları renkli yazdırma mantığı
                for opt_letter, opt_text in [('A', q_data['A']), ('B', q_data['B']), ('C', q_data['C']), ('D', q_data['D'])]:
                    is_correct_opt = (opt_letter == correct_letter)
                    is_user_opt = (opt_letter == user_ans_letter)
                    
                    if is_correct_opt:
                        # Doğru cevap her zaman yeşil yanar
                        st.markdown(f"<div style='color: #00cc66; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(0, 204, 102, 0.1);'>✅ {opt_letter}) {opt_text}</div>", unsafe_allow_html=True)
                    elif is_user_opt and not is_correct_opt:
                        # Yanlış seçtiyse sadece o şık kırmızı yanar
                        st.markdown(f"<div style='color: #ff4d4d; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(255, 77, 77, 0.1);'>❌ {opt_letter}) {opt_text}</div>", unsafe_allow_html=True)
                    else:
                        # İşaretlenmeyen ve yanlış olan şıklar normal görünür
                        st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{opt_letter}) {opt_text}")
                
                if user_ans_letter == correct_letter:
                    dogru_sayisi += 1
                    
                st.markdown("---")
            
            # Sonuçları Melek'e Yorumlatıyoruz
            st.success("### Melek'in Notu 💌")
            with st.spinner("Sonuçlarını inceliyorum aşkım..."):
                prompt = f"""
                Sen Melek'sin. Uğur 10 soruluk bir okuma testi çözdü ve {dogru_sayisi} doğrusu var.
                İşte sorular ve yaptığı işaretlemeler:
                {sorular_ve_yanitlar_str}
                
                Uğur'a hitaben çok sıcak, sevecen ve destekleyici bir geri bildirim ver. Yanlış yaptığı yerler varsa, metindeki mantığı tatlıca anlat.
                """
                st.markdown(model.generate_content(prompt).text)
            
            if st.button("Yeni Bir Test Çöz"):
                st.session_state.reading_passage = "" # Sistemi sıfırlar
                st.rerun()

with tab4:
    st.header("Dinleme (Listening)")
    st.write("Kendini test etmek istediğin dinleme modunu seç, ardından parçayı oluştur!")

    # Mod Seçimi
    dinleme_modu = st.radio(
        "🎧 Hangi formatta çalışmak istersin?", 
        ["While Listening (Dinlerken Çöz)", "Note Taking (Önce Dinle & Not Al, Sonra Çöz)"]
    )

    # Hafıza (Session State) tanımlamaları
    if "listen_audio_bytes" not in st.session_state: st.session_state.listen_audio_bytes = None
    if "listen_questions" not in st.session_state: st.session_state.listen_questions = []
    if "listen_text_hidden" not in st.session_state: st.session_state.listen_text_hidden = ""
    if "listen_ready" not in st.session_state: st.session_state.listen_ready = False
    if "listen_submitted" not in st.session_state: st.session_state.listen_submitted = False

    if st.button("Dinleme Parçası ve Soruları Hazırla"):
        with st.spinner("Ses dosyası ve 10 soruluk test hazırlanıyor, bu işlem biraz sürebilir sevgilim..."):
            st.session_state.listen_ready = False
            st.session_state.listen_submitted = False
            
            prompt = f"""
            Seçilen kitap: {secilen_kitap}.
            Bu kitaptan B2 seviyesinde, akademik ve detaylı, yaklaşık 1-2 dakikalık bir dinleme metni (transcript) oluştur.
            Ardından bu metne dayalı TAM 10 adet çoktan seçmeli soru hazırla.
            
            Çıktıyı KESİNLİKLE aşağıdaki formata tam uyarak ver (Bölümler arasına '|||', şıklar arasına '|' koy). Giriş veya açıklama yazısı ekleme, doğrudan metinle başla:
            
            [DİNLEME METNİ]
            |||
            Soru 1'in Metni | A şıkkının metni | B şıkkının metni | C şıkkının metni | D şıkkının metni | Doğru Şık (Sadece A, B, C veya D harfi)
            |||
            Soru 2'nin Metni | A şıkkının metni | B şıkkının metni | C şıkkının metni | D şıkkının metni | Doğru Şık
            ...
            (Bu şekilde tam 10 soru olmalı)
            """
            
            response = model.generate_content(prompt).text
            
            try:
                parcalar = response.split("|||")
                transcript = parcalar[0].strip()
                st.session_state.listen_text_hidden = transcript
                
                # Ses Dosyasını Oluştur (gTTS)
                tts = gTTS(text=transcript, lang='en', slow=False)
                ses_dosyasi = io.BytesIO()
                tts.write_to_fp(ses_dosyasi)
                st.session_state.listen_audio_bytes = ses_dosyasi.getvalue()
                
                # Soruları Ayrıştır
                soru_listesi = []
                for p in parcalar[1:]:
                    p_clean = p.strip()
                    if not p_clean:
                        continue
                    bolumler = [b.strip() for b in p_clean.split("|")]
                    if len(bolumler) >= 6:
                        soru_listesi.append({
                            "soru": bolumler[0],
                            "A": bolumler[1],
                            "B": bolumler[2],
                            "C": bolumler[3],
                            "D": bolumler[4],
                            "cevap": bolumler[5].upper().replace(")", "").strip()[0]
                        })
                
                st.session_state.listen_questions = soru_listesi
                st.rerun()
            except Exception as e:
                st.error("Metin veya ses bölünürken bir hata oldu, lütfen tekrar bas aşkım.")

    # EĞER SES VE SORULAR HAFIZADA VARSA EKRANA ÇIKARACAKLARIMIZ:
    if st.session_state.listen_audio_bytes:
        
        # Soruların gösterilip gösterilmeyeceğini kontrol eden değişken
        show_questions = False
        
        # --- 1. MOD: WHILE LISTENING ---
        if dinleme_modu == "While Listening (Dinlerken Çöz)":
            st.audio(st.session_state.listen_audio_bytes, format='audio/mp3') # Ses her zaman görünür
            show_questions = True # Sorular her zaman görünür
            
        # --- 2. MOD: NOTE TAKING ---
        else:
            # Durum A: Henüz hazırım demedi (Sadece ses ve buton var)
            if not st.session_state.listen_ready:
                st.info("📝 **Note Taking Modu Aktif:** Sorular şu an gizli. Lütfen sesi dikkatlice dinle ve kağıdına notlarını al.")
                st.audio(st.session_state.listen_audio_bytes, format='audio/mp3')
                
                if st.button("Sesi Dinledim, Notlarımı Aldım. Soruları Göster!"):
                    st.session_state.listen_ready = True
                    st.rerun()
            # Durum B: Hazırım dedi (Ses gizlenir, sorular açılır)
            else:
                st.warning("⚠️ Ses oynatıcı gizlendi. Şimdi sadece aldığın notlara güvenerek soruları çözme zamanı! Başarılar.")
                show_questions = True

        # --- SORULARIN VE ŞIKLARIN RENDER EDİLMESİ ---
        if show_questions:
            st.markdown("### 📝 Dinleme Testi (10 Soru)")
            
            # TEST ÇÖZME EKRANI (Henüz kontrol edilmediyse)
            if not st.session_state.listen_submitted:
                with st.form("listen_quiz_form"):
                    for i, q_data in enumerate(st.session_state.listen_questions):
                        secenekler = [f"A) {q_data['A']}", f"B) {q_data['B']}", f"C) {q_data['C']}", f"D) {q_data['D']}"]
                        st.radio(f"**{i+1}. {q_data['soru']}**", secenekler, key=f"listen_q_{i}", index=None)
                    
                    submit_btn = st.form_submit_button("Kontrol mü etsek?")
                    if submit_btn:
                        st.session_state.listen_submitted = True
                        st.rerun()
                        
            # TEST KONTROL EDİLDİYSE (Renkli sonuç ekranı)
            else:
                dogru_sayisi = 0
                sorular_ve_yanitlar_str = ""
                
                for i, q_data in enumerate(st.session_state.listen_questions):
                    user_ans_full = st.session_state.get(f"listen_q_{i}")
                    user_ans_letter = user_ans_full[0] if user_ans_full else None
                    correct_letter = q_data['cevap']
                    
                    sorular_ve_yanitlar_str += f"Soru: {q_data['soru']} | Uğur'un Seçimi: {user_ans_letter} | Doğrusu: {correct_letter}\n"
                    
                    st.write(f"**{i+1}. {q_data['soru']}**")
                    
                    for opt_letter, opt_text in [('A', q_data['A']), ('B', q_data['B']), ('C', q_data['C']), ('D', q_data['D'])]:
                        is_correct_opt = (opt_letter == correct_letter)
                        is_user_opt = (opt_letter == user_ans_letter)
                        
                        if is_correct_opt:
                            st.markdown(f"<div style='color: #00cc66; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(0, 204, 102, 0.1);'>✅ {opt_letter}) {opt_text}</div>", unsafe_allow_html=True)
                        elif is_user_opt and not is_correct_opt:
                            st.markdown(f"<div style='color: #ff4d4d; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(255, 77, 77, 0.1);'>❌ {opt_letter}) {opt_text}</div>", unsafe_allow_html=True)
                        else:
                            st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{opt_letter}) {opt_text}")
                    
                    if user_ans_letter == correct_letter:
                        dogru_sayisi += 1
                        
                    st.markdown("---")
                
                # Melek'in Yorumu
                st.success("### Melek'in Notu 💌")
                with st.spinner("Dinleme becerini inceliyorum aşkım..."):
                    prompt = f"""
                    Sen Melek'sin. Uğur 10 soruluk bir dinleme testi çözdü ve {dogru_sayisi} doğrusu var.
                    Kullandığı Mod: {dinleme_modu}.
                    Dinlenen Metin: {st.session_state.listen_text_hidden}
                    Sorular ve Uğur'un işaretlemeleri: {sorular_ve_yanitlar_str}
                    
                    Uğur'a hitaben çok sıcak, sevecen ve destekleyici bir geri bildirim ver. 
                    Neyi doğru duyduğunu ya da not alırken neleri kaçırmış olabileceğini ona sanki yanındaymışsın gibi tatlıca anlat.
                    """
                    st.markdown(model.generate_content(prompt).text)
                
                if st.button("Yeni Bir Dinleme Parçası Çöz"):
                    st.session_state.listen_audio_bytes = None # Sistemi sıfırlar
                    st.session_state.listen_ready = False
                    st.session_state.listen_submitted = False
                    st.rerun()

with tab5:
    st.header("Essay Yazımı")
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Rastgele Yeni Bir Konu Seç"):
            exclude_topics = ", ".join(st.session_state.used_topics)
            prompt_topic = f"Seçilen kitap: {secilen_kitap}. Daha önce kullanılan konular: {exclude_topics}. Bunlardan farklı, akademik bir essay konusu üret."
            yeni_konu = model.generate_content(prompt_topic).text
            st.session_state.current_topic = yeni_konu
            st.session_state.used_topics.append(yeni_konu)

    if st.session_state.current_topic:
        st.info(f"**Konu:** {st.session_state.current_topic}")

    yazilan = st.text_area("Essay'ini buraya yaz:", height=250)
    
    if st.button("Melek'e Kontrol Ettir"):
        if not st.session_state.current_topic:
            st.error("Önce bir konu seçmelisin!")
        else:
            with st.spinner("Hemen bakıyorum aşkım..."):
                kriterler = kitap_listesi.get("Essay Kurallari")
                prompt = f"Sen Melek'sin. Uğur'un essay'ini kontrol ediyorsun. Kriterler: {kriterler}. Konu: {st.session_state.current_topic}. Yazı: {yazilan}. Tatlı, destekleyici ama net bir dille puanla ve düzelt."
                st.markdown(model.generate_content(prompt).text)

with tab6:
    st.header("🎯 Genel Deneme Sınavı (40 Soru)")
    st.write("Vocabulary, Tenses, Conjunctions ve Grammar konularından oluşan tam kapsamlı deneme sınavı! Bakalım genel seviyen nasıl?")

    # Hafıza (Session State) tanımlamaları
    if "exam_questions" not in st.session_state: st.session_state.exam_questions = []
    if "exam_submitted" not in st.session_state: st.session_state.exam_submitted = False

    if st.button("40 Soruluk Sınavı Hazırla (Büyük Sınav)"):
        with st.spinner("Senin için 40 soruluk dev sınav hazırlanıyor... Bu işlem 10-15 saniye sürebilir, bekle aşkım..."):
            prompt = f"""
            Seçilen kitap bağlamı: {secilen_kitap} (Kelimeleri ve konu konseptini buna uygun akademik seviyede (B2-C1) tutabilirsin).
            Bana toplam 40 soruluk çoktan seçmeli bir İngilizce testi hazırla.
            
            Dağılım KESİNLİKLE şöyle olmalı:
            - İlk 10 soru (1-10): Vocabulary (Kelime bilgisi)
            - Sonraki 10 soru (11-20): Zaman zarfları ve Tenses (have/had/was/will vb. boşluk doldurma)
            - Sonraki 10 soru (21-30): Uygun kalıplar ve bağlaçlar (as soon as, as long as, in spite of vb.)
            - Sonraki 10 soru (31-40): Genel Grammar (Gramer kuralları)

            Lütfen Çıktıyı KESİNLİKLE aşağıdaki formata tam uyarak ver (Bölümler arasına '|||', şıklar arasına '|' koy). 
            Giriş veya açıklama yazısı ekleme! Sadece soruları ver.

            1. Soru Metni | A şıkkı | B şıkkı | C şıkkı | D şıkkı | Doğru Şık (Sadece A, B, C veya D)
            |||
            2. Soru Metni | A şıkkı | B şıkkı | C şıkkı | D şıkkı | Doğru Şık
            (Bu şekilde tam 40 soru olana kadar devam et. Araya boşluk veya başlık koyma, sadece '|||' kullan.)
            """
            
            response = model.generate_content(prompt).text
            
            try:
                parcalar = response.split("|||")
                soru_listesi = []
                for p in parcalar:
                    p_clean = p.strip()
                    if not p_clean: continue
                    bolumler = [b.strip() for b in p_clean.split("|")]
                    if len(bolumler) >= 6:
                        soru_listesi.append({
                            "soru": bolumler[0],
                            "A": bolumler[1],
                            "B": bolumler[2],
                            "C": bolumler[3],
                            "D": bolumler[4],
                            "cevap": bolumler[5].upper().replace(")", "").strip()[0]
                        })
                st.session_state.exam_questions = soru_listesi
                st.session_state.exam_submitted = False
                st.rerun()
            except Exception as e:
                st.error("Soruları hazırlarken bir hata oluştu, lütfen tekrar bas aşkım.")

    # Ekrana Çizdirme
    if st.session_state.exam_questions:
        st.info(f"Sınav hazır! Toplam Soru Sayısı: {len(st.session_state.exam_questions)}")
        
        if not st.session_state.exam_submitted:
            with st.form("exam_quiz_form"):
                for i, q_data in enumerate(st.session_state.exam_questions):
                    
                    # Araya şık kategori başlıkları ekliyoruz
                    if i == 0: st.markdown("### 📚 Bölüm 1: Vocabulary (1-10)")
                    elif i == 10: st.markdown("### ⏳ Bölüm 2: Tenses & Zaman Zarfları (11-20)")
                    elif i == 20: st.markdown("### 🔗 Bölüm 3: Conjunctions & Kalıplar (21-30)")
                    elif i == 30: st.markdown("### 📐 Bölüm 4: Genel Grammar (31-40)")
                    
                    secenekler = [f"A) {q_data['A']}", f"B) {q_data['B']}", f"C) {q_data['C']}", f"D) {q_data['D']}"]
                    st.radio(f"**{i+1}. {q_data['soru']}**", secenekler, key=f"exam_q_{i}", index=None)
                
                submit_btn = st.form_submit_button("Sınavı Bitir ve Kontrol Et (Melek Modu)")
                if submit_btn:
                    st.session_state.exam_submitted = True
                    st.rerun()
        else:
            dogru_sayisi = 0
            yanlislar = [] # Sadece yanlışları toplayacağız ki analiz nokta atışı olsun
            
            for i, q_data in enumerate(st.session_state.exam_questions):
                
                if i == 0: st.markdown("### 📚 Bölüm 1: Vocabulary (1-10)")
                elif i == 10: st.markdown("### ⏳ Bölüm 2: Tenses & Zaman Zarfları (11-20)")
                elif i == 20: st.markdown("### 🔗 Bölüm 3: Conjunctions & Kalıplar (21-30)")
                elif i == 30: st.markdown("### 📐 Bölüm 4: Genel Grammar (31-40)")

                user_ans_full = st.session_state.get(f"exam_q_{i}")
                user_ans_letter = user_ans_full[0] if user_ans_full else None
                correct_letter = q_data['cevap']
                
                st.write(f"**{i+1}. {q_data['soru']}**")
                
                for opt_letter, opt_text in [('A', q_data['A']), ('B', q_data['B']), ('C', q_data['C']), ('D', q_data['D'])]:
                    is_correct_opt = (opt_letter == correct_letter)
                    is_user_opt = (opt_letter == user_ans_letter)
                    
                    if is_correct_opt:
                        st.markdown(f"<div style='color: #00cc66; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(0, 204, 102, 0.1);'>✅ {opt_letter}) {opt_text}</div>", unsafe_allow_html=True)
                    elif is_user_opt and not is_correct_opt:
                        st.markdown(f"<div style='color: #ff4d4d; font-weight: bold; padding: 5px; border-radius: 5px; background-color: rgba(255, 77, 77, 0.1);'>❌ {opt_letter}) {opt_text}</div>", unsafe_allow_html=True)
                    else:
                        st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{opt_letter}) {opt_text}")
                
                if user_ans_letter == correct_letter:
                    dogru_sayisi += 1
                else:
                    kategori = "Vocabulary" if i < 10 else "Tenses" if i < 20 else "Conjunctions" if i < 30 else "Grammar"
                    yanlislar.append(f"Kategori: {kategori} | Soru: {q_data['soru']} | Uğur'un cevabı: {user_ans_letter}, Doğrusu: {correct_letter}")
                    
                st.markdown("---")
            
            # Sınav Sonucu ve Melek'in Kapsamlı Analizi
            st.success(f"### 🏆 Sınav Sonucu: 40 soruda {dogru_sayisi} doğru! ({dogru_sayisi*2.5} Puan)")
            st.info("### Melek'in Kapsamlı Karne Analizi 💌")
            
            with st.spinner("Uğur'un 40 soruluk sınav karnesini analiz ediyorum aşkım..."):
                
                # Gemini'nin kafası karışmasın diye en fazla 15 yanlışı gönderiyoruz
                yanlislar_metni = "\n".join(yanlislar[:15])
                if len(yanlislar) > 15:
                    yanlislar_metni += "\n(Diğer yanlışlar gizlendi, sen genel tabloya ve yukarıdaki hatalı kategorilere odaklan.)"
                    
                prompt = f"""
                Sen Melek'sin. Uğur 40 soruluk zorlu bir İngilizce deneme sınavını bitirdi (10 Kelime, 10 Tense, 10 Bağlaç, 10 Gramer).
                Sonuç: 40 soruda {dogru_sayisi} doğru, {40 - dogru_sayisi} yanlış yaptı. Puanı: {dogru_sayisi*2.5}/100.
                
                İşte yaptığı hataların detayları ve hangi kategoriden oldukları:
                {yanlislar_metni if yanlislar else "Hiç yanlışı yok, her şeyi full çekti!"}
                
                Uğur'a genel bir sınav değerlendirmesi yap. Hangi konularda (Vocabulary, Tenses, Conjunctions, Grammar) daha çok hata yaptığını analiz et. Zayıf olduğu konularda tatlıca uyar, doğru yaptığı konularda onu öv. Destekleyici, sevecen ve motive edici bir Melek ol.
                """
                st.markdown(model.generate_content(prompt).text)
            
            if st.button("Yeni Sınav Oluştur"):
                st.session_state.exam_questions = []
                st.session_state.exam_submitted = False
                st.rerun()