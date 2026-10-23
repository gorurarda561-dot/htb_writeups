# HTB Bedside | Full Attack Chain Walkthrough

**Zorluk:** Medium | **OS:** Linux | **Kategori:** Web / ML Pipeline Abuse

## Genel Bakış

Bedside, bir araştırma portalını hedef alan çok katmanlı bir web ve iç ağ saldırı zinciri barındırıyor:

Virtual Host Enumeration → Dosya Yükleme Portalı üzerinden foothold → PDF işleme pipeline'ı → İç ağda SSRF/Path Traversal ile SSH private key sızıntısı → Yatay hareket → 
ML checkpoint yükleme akışında güvensiz pickle/torch deserialization → Root.

## Saldırı Yolu

- Nmap port taraması ve /etc/hosts kaydı 
- Virtual Host Fuzzing (ffuf) → research.bedside.htb keşfi
- Gobuster dizin taraması → /uploads/ endpoint'i
- Dosya yükleme portalı → PDF işleme pipeline'ı (pdf_watcher.py) üzerinden foothold (datawrangler)
- İç ağda (172.17.0.1:3000) SSRF + Path Traversal → /etc/passwd ve developer kullanıcısının SSH private key'i sızıntısı
- SSH ile developer kullanıcısına yatay hareket → user.txt
- /datastore/checkpoints dizinine pickle dosyası bırakma (dataops grup yazma izni)
- sudo ile çalıştırılabilen bedside_trainer.py (MONAI/Ignite CheckpointLoader) → torch.load() üzerinden pickle deserialization → Root


---

