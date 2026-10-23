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

## Recon (Keşif)

### 1 — Host ayakta mı?

```bash
ping -c 4 10.129.177.38
```

![ping](images/01.png)

Ping komutu ile hedefin ağ üzerinden erişilebilir durumda olup olmadığına bakıyoruz.

**Not:** TTL değeri 63 olarak görüldü — bu, hedefin bir Linux sistemi olduğuna dair ilk ipucu.

### 2 — Nmap Port/Service/OS Taraması

```bash
nmap -A -Pn 10.129.177.38
```

![nmap taraması](images/02.png)

- **22/tcp** → `tcpwrapped` (SSH, ama banner gizli/filtreli).
- **80/tcp** → `tcpwrapped`, ancak HTTP başlığında `Apache/2.4.68 (Debian)` görünüyor.
- **3000/tcp filtered** → dışarıdan erişime kapalı/filtrelenmiş olarak gözüküyor.

### 3 — /etc/hosts Kaydı

```bash
echo "10.129.177.38 bedside.htb" | sudo tee -a /etc/hosts
```

![etc hosts](images/03.png)


### 4 — Virtual Host Fuzzing (ffuf)

```bash
ffuf -u http://bedside.htb/ -H "Host: FUZZ.bedside.htb" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -ac
```

![ffuf vhost](images/04.png)

`Host:` header'ını fuzzlayarak sunucuda tanımlı olabilecek başka **virtual host'ları** (subdomain) arıyoruz.
**Not:** -ac (auto-calibrate) ile yanlış pozitifler'i otomatik olarak eliyor.
Sonuç: **`research`** subdomaini 200 OK dönüyor. 


### 5 — /etc/hosts Kaydı (research.bedside.htb)

```bash
echo "10.129.177.38 research.bedside.htb" | sudo tee -a /etc/hosts
```

![etc hosts research](images/05.png)

ffuf ile bulduğumuz `research.bedside.htb` vhost'una tarayıcıdan erişebilmek için bu kaydı da `/etc/hosts`'a ekliyoruz.


### 6 — Gobuster Dizin Taraması

```bash
gobuster dir -u http://research.bedside.htb -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
```

![gobuster](images/06.png)

`research.bedside.htb` üzerinde gizli dizin/endpoint'leri aramak için gobuster çalıştırıyoruz. Sonuçlar:

- `/uploads/` (301) — yüklenen dosyaların tutulduğu dizin
- `/javascript/` (301)
- `/server-status` (403) — erişim engellenmiş

`/uploads/` bulgusu, sitede bir **dosya yükleme fonksiyonu** olduğuna işaret ediyor.


### 7 — Ana Sayfayı (bedside.htb) İnceleme

![bedside ana sayfa](images/07.png)


### 8 — Research Portal'ı İnceleme

![research portal](images/08.png)

Burası **"Bedside Research Portal"** adında bir dosya yükleme arayüzü.
Kabul ettiği formatlar: `jpeg, jpg, png, bmp, tiff, dcm, pdf`.


---

## Foothold — Dosya Yükleme ve Reverse Shell

### 9 — Payload Hazırlama ve Yükleme

![payload hazırlama](images/09.png)

`bedsidee.py` scriptiyle bir reverse shell komutu barındıran kötücül bir pickle payload'ı oluşturuyoruz (`shell.pickle.gz`). Ardından `trigger.py` scriptiyle bu payload'ı araştırma portalına yüklüyoruz — `sh.pickle.gz` ve `trigger.pdf` olarak yükleniyor ve arka planda çalışan **cron/watcher** sürecinin bunu işlemesini (`~30s` içinde) bekliyoruz.


### 10 — Reverse Shell 

```bash
nc -lvnp 9000
```

![reverse shell](images/10.png)

Watcher süreci payload'ı işlediğinde bağlantı geliyor.

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

ardından `Ctrl+Z` ile arka plana alıp `stty raw -echo; fg` ile terminali tam etkileşimli hale getiriyoruz.


### 11 — Dosya Sistemi Keşfi

![requirements ve ls](images/11.png)

```bash
cat requirements.txt
```

`pdfminer.six==20250506` paketi görülüyor — watcher, PDF dosyalarını `pdfminer` ile parse ediyor. Kök dizine çıkıp (`cd ..`, `ls -la`) genel yapıyı inceliyoruz.
`sudo -l` denemesi bu noktada sonuç vermiyor.

























