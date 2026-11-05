# InkProf Soft Proof

Handbok - version 2.1.2 - 5 november 2026

Christer Törnkvist - christer@borgasundsfotografiska.se
GNU GPL version 3 eller senare (GPL-3.0-or-later).

## 1. Installera och kom igång

InkProf Soft Proof jämför en bild med en beräknad simulering av dess utskrift. Du kan undersöka följderna av vald arbetsfärgrymd, skrivar-/pappersprofil, återgivningsmetod och svartpunktskompensation innan du sparar en konverterad bild.

### Installera appen

Öppna `InkProfSoftProof-2.1.2-arm64.dmg`, dra **InkProf Soft Proof.app** till **Applications / Program**, mata ut skivavbilden och starta appen från Program. Det fristående paketet är för **Apple Silicon och macOS 14 eller senare**. Python och nödvändiga bibliotek ingår; utvecklingsprojektet behövs inte.

Paketet är ad hoc-signerat men saknar Developer ID-signering och Apple-notarisering. Om macOS blockerar första starten, granska appen i **Systeminställningar > Integritet och säkerhet > Öppna ändå**. DMG-filen innehåller båda handböckerna, GPL-licensen och appens källkod.

### Börja med en känd bild

Välj **Öppna bild**, välj sedan arbetsfärgrymd och skrivar-/pappersprofil. Originalet visas till vänster och den aktuella simuleringen till höger. En bild utan profil behöver en uttryckligen vald källprofil för att dess färger ska kunna tolkas.

<!-- pipeline -->

Konverteringskedjan är: **källprofil > arbetsfärgrymd > skrivar-/pappersprofil**. En separat visningskonvertering förbereder simuleringen för skärmen; macOS ColorSync anpassar den profilmärkta bilden till aktuell bildskärm.

### Använd rätt fysisk uppsättning

Välj ICC-profil för den verkliga skrivaren, papperet, bläcket och drivrutinsinställningarna. Bildskärmens kalibrering och ljuset där utskriften betraktas påverkar jämförelsen. Soft proof är en profilbaserad uppskattning, inte en mätning eller garanti för en matchande utskrift.

## 2. Profiler och återgivning

### Källprofil och arbetsfärgrymd

En inbäddad ICC-profil används alltid som källa. För en bild utan profil väljer du den profil som verkligen beskriver bildens lagrade värden. Denna tilldelade tolkning ändrar inte originalfilen. Fel källprofil ändrar innebörden av alla färger.

Menyn erbjuder sRGB, Adobe RGB (1998), Display P3, ProPhoto RGB och en egen ICC-profil. ProPhoto RGB använder systemprofilen ROMM RGB i macOS. **Behåll bildens färgrymd** undviker en onödig omräkning via arbetsfärgrymd. Vald återgivningsmetod och svartpunktskompensation används både vid konvertering till arbetsfärgrymden och därifrån till skrivarprofilen.

| Återgivningsmetod | Praktisk innebörd |
| --- | --- |
| Relativ kolorimetrisk | Anpassar vitt till målet och mappar färger som ligger utanför dess omfång. |
| Absolut kolorimetrisk | Bevarar absolut kolorimetri, inklusive profilernas vitpunktsförhållande. |
| Perceptuell | Använder profilens perceptuella mappning, om den finns, för att bevara visuella relationer. |

Olika metoder kan ge samma resultat när profilen inte har skilda mappningar.

### Svartpunktskompensation och pappersvitt

**Svartpunktskompensation** anpassar mappningen av mörka toner mellan profiler. Den synliga effekten beror på profilerna och återgivningsmetoden.

**Simulera pappersvitt** är en separat skärminställning. Den väljer absolut kolorimetrisk återgivning från proofprofil till visningsrymd; konverteringsmetoden till skrivaren är ett eget led. Inställningen påverkar förhandsvisningen, inte de sparade skrivarvärdena.

### Skärmens färghantering

Förhandsvisningen är en ICC-märkt Display P3-bild som visas genom macOS AppKit/ColorSync. Operativsystemet anpassar den till skärmen där fönstret visas, även vid flytt mellan skärmar. Välj inte skärmprofilen som arbets- eller skrivarprofil. Display P3 kan i sig begränsa färger utanför denna mellanliggande visningsrymd.

## 3. Jämför och välj en färg

### Jämförelse sida vid sida

Vänster vy börjar som originalet tolkat med källprofilen. Höger vy följer den aktuella arbetsfärgrymden och skrivarinställningarna. Utan skrivarprofil visar höger vy enbart arbetsfärgrymdens konvertering.

Välj **Lås simulering som referens** för att behålla resultat A till vänster. Ändra profiler, återgivningsmetod eller kompensation för att skapa resultat B till höger. Referensens bildtext bevarar inställningarna som användes för A. **Visa original till vänster** återgår till originaljämförelsen.

### Zoom och rullning

Båda vyerna har gemensam zoom och rullning. **Anpassa** visar hela bilden; 25 %, 50 % och 100 % använder originalets mått som storleksreferens. Förhandsvisningen begränsas till 2 000 pixlar på längsta sidan. För större original kan 100 % därför förstora den reducerade bilden; det är inte pixelgranskning i full upplösning.

### Klicka för att välja färgprov

Klicka i någon av bildvyerna för att öppna färgomfångsfönstret och följa motsvarande originalpixel. Ett hårkors markerar positionen i båda vyerna. Provet läses ur originalfilen efter eventuell EXIF-orientering, oberoende av zoom och förhandsvisningens nedsampling.

Klick i en låst referens följer fortfarande originalpixeln genom de **aktuella** profilinställningarna. Referensens gamla konvertering samplas inte. Ändrade inställningar uppdaterar samma valda pixel. En ny bild rensar referensen och färgprovet.

### Läs värdena för varje steg

Färgomfångsfönstret redovisar källvärden, arbetsfärgrymd och förväntade skrivarvärden. RGB- eller CMYK-värden kan ändras medan Lab-positionen ligger nästan stilla: en färgbevarande konvertering försöker bevara färgen, inte samma tal. En förflyttning visar en beräknad färgändring, exempelvis genom ommappning till annat omfång eller 8-bitarskvantisering.

## 4. Läs färgomfångsdiagrammet

Alla profiler jämförs i **CIELAB D50**. Välj a*/b* ovanifrån, a*/L* framifrån eller b*/L* från sidan. Axelvärdena har samma skala per enhet och utvidgas vid behov utan att krympa när du ändrar inställningar.

<!-- gamut -->

### Konturer, punkter och pilar

Konturerna visar käll-, arbets- och skrivarprofil. Dölj dem var för sig för en tydligare vy. Numrerade punkter och pilar följer **original > arbetsfärgrymd > förväntad utskrift**. Grå ringar visar föregående inställning för samma pixel.

Sifferraderna visar L*, a*, b*, kanalvärden och **ΔE76 från originalet**. Lab beräknas genom LittleCMS med flyttalsutgång och fast absolut D50-kolorimetri. Kanalomräkningen följer samma 8-bitarsflöde som exporten. Skrivarens punkt är profilens förutsägelse, inte en uppmätt utskrift. Skärmprofilen och reglaget för pappersvitssimulering ingår inte i dessa analyskoordinater.

### Ungefärligt färgad bakgrund

**Färgtonad bakgrund** ger en kulörguide; **Styrka** justerar tydligheten. I a*/b* används originalprovets L*, eller 65 innan ett prov valts. Sidovyerna håller b*=0 respektive a*=0. Det är färgade snitt bakom projicerade konturer, inte en mätning av alla färger i projektionen. Skärmens begränsningar och toningen gör bakgrunden approximativ.

### Konturen är inget exakt omfångstest

Konturerna är konvexa ytterhöljen av samplade ICC-enhetsvärden, projicerade till ett plan. Den tredje dimensionen sammanförs och konkava delar kan överskattas. Samplingen använder 17 nivåer per RGB-/Lab-kanal och 9 per CMYK-kanal, utan separat begränsning av totalfärg i CMYK. En punkt innanför konturen bevisar inte att färgen kan skrivas ut vid sitt L*.

## 5. Spara och skriv ut

Välj **Konvertera och spara** när en bild och en skrivar-/pappersprofil är valda. Appen bearbetar hela bilden via arbetsfärgrymden och skrivarprofilen och bäddar sedan in vald ICC-fil **byte för byte**. Originalbilden får inte skrivas över.

| Format | Utkanaler som stöds |
| --- | --- |
| TIFF | RGB, RGBA, CMYK, gråskala, gråskala med alfa, Lab |
| PNG | RGB, RGBA, gråskala, gråskala med alfa |
| JPEG | RGB, CMYK, gråskala; ingen alfa; förstörande komprimering |

En oförenlig kombination av kanaler och format stoppas. Transparens kan bevaras vid RGB- eller gråskalebearbetning; CMYK-/Lab-konvertering med alfa stoppas. Transparenta färgprov analyseras före blandning mot en bakgrund, och alfa redovisas separat.

### Skriv ut de konverterade värdena en gång

Exportbilden är redan konverterad till skrivarprofilen. Skriv ut dessa värden med ytterligare färgkonvertering avstängd i program, operativsystem och drivrutin. Använd samma skrivare, papper, medie- och kvalitetsinställningar som ICC-profilen. Appen exporterar filer; den styr eller verifierar inte drivrutinen eller den fysiska utskriftskedjan.

### Versionens begränsningar

Appen stöder en bildruta och **8 bitar per kanal**. Export bevarar hela bildens pixelmått, ICC-profil, DPI och alfa där formatet stöder det. All EXIF/XMP eller övrig metadata bevaras inte. JPEG är förstörande. Pappersvitssimuleringen bakas inte in i exporten. Förhandsvisningens gräns på 2 000 pixlar minskar inte exportens mått.

En lyckad export eller en liten förutsagd ΔE visar inte uppmätt utskriftsnoggrannhet. Bedöm viktiga arbeten med en korrekt förberedd fysisk provutskrift.

## 6. Språk, arkitektur och licens

### Språk och avslut

Välj **Svenska** eller **English** vid **Språk / Language**. Båda fönstren, menyer, statusmeddelanden och appens egna feltexter uppdateras direkt. Profilval, färgprov och låst referens bevaras. Valet återställs vid nästa start. Profilnamn och filnamn översätts inte; macOS egna knappar och systemfel kan följa systemspråket.

**Avsluta** finns längst ned till höger i huvudfönstret. Du kan även använda appmenyn eller Kommando-Q.

### ARM, Intel och Rosetta

Nederst skiljer appen på datorns hårdvara, Python-processens arkitektur och direkt körning respektive Rosetta. Rosetta läses i själva Python-processen. Uppgifter som inte kan fastställas visas som **Okänd**. Klassificeringen av native ARM, native Intel och Rosetta testas; själva installationspaketet är ARM64 och verifierat på Apple Silicon.

### GPL-licens och kontakt

Copyright (c) 2026 **Christer Törnkvist**.
E-post: **christer@borgasundsfotografiska.se**.

Programmet och dokumentationen är fri programvara under **GNU General Public License, version 3 eller valfri senare version** (GPL-3.0-or-later). De tillhandahålls utan garanti. Den fullständiga, oförändrade licensen finns i **LICENSE**. Tredjepartskod, systemresurser och typsnitt behåller sina egna villkor; se **LICENSE_SCOPE.md** och **THIRD_PARTY_NOTICES.md**.

Appmenyn har **Om InkProf Soft Proof** med namn, kontakt och licensinformation samt **Visa GPL-licensen** som öppnar hela texten. DMG-filen innehåller appens källkod, byggverktyg och båda handböckerna. README på engelska beskriver källkodsinstallation, tester och hur DMG-paketet byggs om. Personliga fotografier, mätningar och lokala Python-miljöer ingår inte i Git-repositoryn eller källkodsarkivet.
