/**
 * BIST Dashboard Kimlik Doğrulama Yapılandırması
 * BU DOSYA GIT'E COMMIT EDİLMEZ (.gitignore listesindedir).
 * 
 * Varsayılan Şifre: bist2026
 * 
 * Şifrenizi değiştirmek için:
 * Tarayıcı konsolunda `createPasswordHash('YENI_SIFRENIZ')` komutunu çalıştırın
 * ve üretilen SHA-256 kodunu kopyalayıp aşağıdaki passwordHash alanına yapıştırın.
 */
window.AUTH_CONFIG = {
  // "bist2026" şifresinin SHA-256 hash karşılığı:
  passwordHash: "70be4c693915a05f0b501204e2fccda891e7ae9a23d237ad60b00a7ab4b04bec",
  
  // Site başlığı
  siteTitle: "BIST Terminal",
  
  // Beni hatırla seçildiğinde oturum süresi (gün)
  rememberMeDays: 7
};
