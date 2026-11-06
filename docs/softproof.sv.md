# SoftProf

Handbok - version 2.4.1 - 6 november 2026

Christer Törnkvist - christer@borgasundsfotografiska.se
GNU GPL version 3 eller senare (GPL-3.0-or-later).

## 1. Installera och kom igång

SoftProf jämför en bild med en beräknad simulering av dess utskrift. Du kan undersöka följderna av vald arbetsfärgrymd, skrivar-/pappersprofil, återgivningsmetod och svartpunktskompensation innan du sparar en konverterad bild.

### Installera appen

Öppna `SoftProf-2.4.1-macos.dmg`, välj **Apple Silicon** eller **Intel** efter datorns processor och dra den appen till **Applications / Program**, mata ut skivavbilden och starta appen från Program. DMG-filen har två märkta appar: **Apple Silicon kräver macOS 14+; Intel kräver macOS 13 Ventura+**. Apple Silicon är ARM64; Intel är x86_64. Alla Intel-binärer kontrolleras mot Venturas systemkrav. Fysisk Ventura-maskin har inte testats här. Installera bara rätt app för din dator. Python och nödvändiga bibliotek ingår; utvecklingsprojektet behövs inte.

Paketet är ad hoc-signerat men saknar Developer ID-signering och Apple-notarisering. Om macOS blockerar första starten, granska appen i **Systeminställningar > Integritet och säkerhet > Öppna ändå**. DMG-filen innehåller båda handböckerna, GPL-licensen och appens källkod.

### Välj rätt app för din dator

| Dator | App och märkning |
| --- | --- |
| Apple Silicon, exempelvis M1, M2 eller M3 | SoftProf - Apple Silicon.app, märkt ARM64 |
| Intel-processor | SoftProf - Intel.app, märkt INTEL |

Kontrollera processorn i **Apple-menyn > Om den här datorn** om du är osäker. Installera en app. ARM64-appen körs direkt utan Rosetta på Apple Silicon; Intel-appen körs direkt på en Intel-Mac. Rosetta används bara i vårt test av Intel-versionen på Apple Silicon.

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

**Simulera trycksvärta** bevarar skrivarprofilens förutsagda svartnivå. Stäng av valet, med pappersvitt avstängt, för att mappa svart till skärmsvart. Pappersvitt aktiverar även trycksvärta. Dessa visningsval ändrar inte exporten. Förhandsvisningen använder samma 8- eller 16-bitars skrivarvärden som exporten; LittleCMS optimering är avstängd för att undvika extra interpolationsfel. JPEG-export kan ge ytterligare förändringar.

### Skärmens färghantering

Förhandsvisningen är en ICC-märkt Display P3-bild som visas genom macOS AppKit/ColorSync. Operativsystemet anpassar den till skärmen där fönstret visas, även vid flytt mellan skärmar. Välj inte skärmprofilen som arbets- eller skrivarprofil. Display P3 kan i sig begränsa färger utanför denna mellanliggande visningsrymd.

## 3. Jämför och välj en färg

### Jämförelse sida vid sida

Vänster vy börjar som originalet tolkat med källprofilen. Höger vy följer den aktuella arbetsfärgrymden och skrivarinställningarna. Utan skrivarprofil visar höger vy enbart arbetsfärgrymdens konvertering.

Välj **Lås simulering som referens** för att behålla resultat A till vänster. Ändra profiler, återgivningsmetod eller kompensation för att skapa resultat B till höger. Referensens bildtext bevarar inställningarna som användes för A. **Visa original till vänster** återgår till originaljämförelsen.

### Zoom och rullning

Båda vyerna har gemensam zoom och rullning. **Anpassa** visar hela bilden; 25 %, 50 % och 100 % använder originalets mått. Förhandsvisningen bevarar alla pixlar, så 100 % förstorar inte längre en reducerad bild. Vid 100 % motsvarar en bildpixel en fysisk skärmpixel, med hänsyn till Retina-skalning. Stora bilder kräver mer minne och tar längre tid att bearbeta.

### Klicka för att välja färgprov

Klicka i någon av bildvyerna för att öppna färgomfångsfönstret och följa motsvarande originalpixel. Ett hårkors markerar positionen i båda vyerna. Provet läses ur originalfilen efter eventuell EXIF-orientering, oberoende av zoom.

Klick i en låst referens följer fortfarande originalpixeln genom de **aktuella** profilinställningarna. Referensens gamla konvertering samplas inte. Ändrade inställningar uppdaterar samma valda pixel. En ny bild rensar referensen och färgprovet.

### Läs värdena för varje steg

Färgomfångsfönstret redovisar källvärden, arbetsfärgrymd och förväntade skrivarvärden. RGB- eller CMYK-värden kan ändras medan Lab-positionen ligger nästan stilla: en färgbevarande konvertering försöker bevara färgen, inte samma tal. En förflyttning visar en beräknad färgändring, exempelvis genom ommappning till annat omfång eller kvantisering.

## 4. Läs färgomfångsdiagrammet

Alla profiler jämförs i **CIELAB D50**. Den vanliga 2D-vyn visar a*/b*-planet ovanifrån. Axelvärdena har samma skala per enhet och utvidgas vid behov utan att krympa när du ändrar inställningar.

<!-- gamut -->

### Konturer, punkter och pilar

Konturerna visar käll-, arbets- och skrivarprofil. Dölj dem var för sig för en tydligare vy. Numrerade punkter och pilar följer **original > arbetsfärgrymd > förväntad utskrift**. Grå ringar visar föregående inställning för samma pixel.

Sifferraderna visar L*, a*, b*, kanalvärden och **ΔE76 från originalet**. Lab beräknas genom LittleCMS med flyttalsutgång och fast absolut D50-kolorimetri. Kanalomräkningen följer samma 8- eller 16-bitarsflöde som exporten. Skrivarens punkt är profilens förutsägelse, inte en uppmätt utskrift. Skärmprofilen och reglaget för pappersvitssimulering ingår inte i dessa analyskoordinater.

### Ungefärligt färgad bakgrund

**Färgtonad bakgrund** ger en kulörguide; **Styrka** justerar tydligheten. Avmarkera **Följ färgprovets L*** för att välja bakgrundens ljushet från **0 till 100** med reglaget eller sifferfältet (tryck Retur). L* 0 är svart och 100 är vitt. Markera valet för att följa originalprovets L*, eller 65 innan ett prov valts. Bara bakgrunden ändras, inte färgprov, konturer eller export. Bakgrunden är ett färgat snitt vid vald L* bakom de projicerade konturerna, inte en mätning av alla färger i projektionen. Skärmens begränsningar och toningen gör bakgrunden approximativ.

### Konturen är inget exakt omfångstest

Konturerna är konvexa ytterhöljen av samplade ICC-enhetsvärden, projicerade till ett plan. Den tredje dimensionen sammanförs och konkava delar kan överskattas. Samplingen använder 17 nivåer per RGB-/Lab-kanal och 9 per CMYK-kanal, utan separat begränsning av totalfärg i CMYK. En punkt innanför konturen bevisar inte att färgen kan skrivas ut vid sitt L*.

## 5. 3D-färgrymd och förflyttning

Välj **Visa 3D-färgrymd**; **Visa 2D** återgår till diagrammet. Välj **Original**, **Arbetsfärgrymd** eller **Utskrift** i 3D-vyns meny. Dra för att rotera, rulla för att zooma eller välj **Återställ 3D-vy**. L* ökar uppåt mot ljusare färger, a* går från grönt (negativt) till rött (positivt) och b* från blått (negativt) till gult (positivt). Följ axlarnas märkning när vyn roteras. Bildens valda pixel markeras med en vit ring i valt steg. L*-reglaget för bakgrunden gäller bara 2D.

Markera **Visa förflyttning** och ändra arbetsfärgrymd, skrivarprofil, återgivningsmetod eller BPC i huvudfönstret. Samma representanter animeras från föregående till nya lägen; tydligt gula pilar finns kvar för jämförelse. Pilspetsarna pekar mot det nya resultatet. Texten under diagrammet förklarar riktningen och anger arbetsfärgrymd och visat steg före och efter ändringen, även när färgrymden byts. Byte av 3D-vyns steg visar också förflyttningen. Avmarkera för en statisk vy. Färgbevarande konvertering kan ge mycket små rörelser; pappersvitt och trycksvärta ändrar inte absoluta Lab-positioner.

3D-vyn visar upp till 1 024 vanliga grupper ur högst 65 536 reproducerbart samplade pixlar. Närliggande källkanalvärden grupperas och en faktisk originalpixel representerar varje grupp. De mindre punkterna gör täta områden tydligare; punktstorleken ökar fortfarande med ungefärlig samplad förekomst; helt genomskinliga pixlar utelämnas och delvis alfa viktar förekomsten. Ovanliga färger kan utelämnas. Punkterna är bildens fördelning, inte ett helt profilomfång eller volymskal. Punkternas Display P3-skärmfärger är approximativa. Originalbilderna ändras inte.

<!-- cloud -->

## 6. Spara och skriv ut

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

Appen stöder en bildruta och **8 eller osignerade 16 bitar per kanal**. För 16-bitarsbilder använder RGB/RGBA och gråskala/alfa TIFF eller PNG; CMYK använder TIFF. TIFF stöder okomprimerat, LZW, Deflate/ZIP och PackBits, separata kanalplan och orientering. ICC-konvertering, valda pixlar, 3D-positioner och TIFF/PNG-export bevarar 16-bitars precision. Kanalvärdena går från 0 till 65 535 i stället för 0 till 255. JPEG är bara 8 bitar och kan inte väljas för 16-bitarsoriginal. Filer med 16-bitars Lab och 32-bitars/flyttalsbilder stöds inte; en Lab-arbetsprofil fungerar fortfarande. Export bevarar pixelmått, ICC, DPI och stödd alfa, inte all EXIF/XMP. Pappersvitt och trycksvärta bakas inte in i exporten.

En lyckad export eller en liten förutsagd ΔE visar inte uppmätt utskriftsnoggrannhet. Bedöm viktiga arbeten med en korrekt förberedd fysisk provutskrift.

En numerisk jämförelse med Photoshop 27.11 hittade och rättade ett optimeringsfel i mörka toner. Kvarvarande skillnader redovisas i färgkontrollrapporten på GitHub. Detta verifierar inte Photoshops korrekturvisning på skärmen eller fysisk utskriftsnoggrannhet.

## 7. Språk, arkitektur och licens

### Språk och avslut

Välj **Svenska** eller **English** vid **Språk / Language**. Båda fönstren, menyer, statusmeddelanden och appens egna feltexter uppdateras direkt. Profilval, färgprov och låst referens bevaras. Valet återställs vid nästa start. Profilnamn och filnamn översätts inte; macOS egna knappar och systemfel kan följa systemspråket.

**Avsluta** finns längst ned till höger i huvudfönstret. Du kan även använda appmenyn eller Kommando-Q.

### ARM, Intel och Rosetta

Nederst skiljer appen på datorns hårdvara, Python-processens arkitektur och direkt körning respektive Rosetta. Rosetta läses i själva Python-processen. Uppgifter som inte kan fastställas visas som **Okänd**. Klassificeringen av native ARM, native Intel och Rosetta testas; DMG-filen innehåller separata ARM64- och x86_64-appar med strikt kontroll av binärerna. ARM64 testas direkt; Intel testas via Rosetta på Apple Silicon, inte på en fysisk Intel-Mac.

### GPL-licens och kontakt

Copyright (c) 2026 **Christer Törnkvist**.
E-post: **christer@borgasundsfotografiska.se**.

Programmet och dokumentationen är fri programvara under **GNU General Public License, version 3 eller valfri senare version** (GPL-3.0-or-later). De tillhandahålls utan garanti. Den fullständiga, oförändrade licensen finns i **LICENSE**. Tredjepartskod, systemresurser och typsnitt behåller sina egna villkor; se **LICENSE_SCOPE.md** och **THIRD_PARTY_NOTICES.md**.

Appmenyn har **Om SoftProf** med namn, kontakt och licensinformation samt **Visa GPL-licensen** som öppnar hela texten. DMG-filen innehåller appens källkod, byggverktyg och båda handböckerna. README på engelska beskriver källkodsinstallation, tester och hur DMG-paketet byggs om. Personliga fotografier, mätningar och lokala Python-miljöer ingår inte i Git-repositoryn eller källkodsarkivet.

---

GitHub: [chto0703009/SoftProf](https://github.com/chto0703009/SoftProf)
