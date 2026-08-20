import streamlit as st

# Sayfa sekme ayarı (Tarayıcıda üstte görünecek)
st.set_page_config(page_title="Erişim Engeli", page_icon="🚫")

# Metni ekranın tam ortasına almak için boşluk bırakıyoruz
st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# Çarpıcı bir hata başlığı
st.error("## 🚫 Erişim Engellendi")

st.markdown("---")

# Senin o muazzam metnin
st.markdown("""
### Sana özel inşa edilen bu alan, bizzat senin tarafından yıkıldı. 

Ne kadar şanslı olduğunu fark etmen ve neyi kaybettiğini görmen için bu enkazı bilerek burada bırakıyorum. 

İçerde seni ilgilendiren hiçbir şey kalmadı.
""")