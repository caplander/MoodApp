async function renderMonthlyHeatmap() {
  // 1) API’den veriyi çek
  const res       = await fetch("/api/mood-data");
  const json      = await res.json();
  const data      = Array.isArray(json.data) ? json.data : [];

  // 2) date → { color, moods[] } map’ini kur
  const dataMap = new Map();
  data.forEach(item => {
    // API’den "YYYY-MM-DD" formatında teslim ediliyor varsayımıyla
    const key = item.date.split("T")[0];
    const moods = Array.isArray(item.moods)
      ? item.moods
      : (item.moods ? item.moods.split(",") : []);
    
    if (!dataMap.has(key)) {
      dataMap.set(key, {
        color: item.color,
        moods: [...moods]
      });
    } else {
      dataMap.get(key).moods.push(...moods);
    }
  });

  // 3) Container’ı temizle ve grid sınıfı ekle
  const container = document.getElementById("heatmapChart");
  container.innerHTML = "";
  container.className = "heatmap";

  // 4) Ayın gün sayısını ve ilk gün tarihini hesapla
  const today       = new Date();
  const todayKey   = today.toISOString().slice(0,10);  // "YYYY-MM-DD"
  const startDate   = new Date(today.getFullYear(), today.getMonth(), 1);
  const daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();

  // 5) Hücreleri oluştur
  for (let i = 0; i < daysInMonth; i++) {
    const d     = new Date(startDate);
    d.setDate(d.getDate() + i);
    const key   = d.toISOString().slice(0,10);
    const entry = dataMap.get(key);

    const cell = document.createElement("div");
    cell.className = "heat-cell";
    // Eğer bugünse, ekstra sınıf ekle
    if (key === todayKey) {
      cell.classList.add("today-cell");
    }
    cell.style.backgroundColor = entry?.color || "#eee";
    cell.title    = entry
      ? `${key}\n${entry.moods.join(", ")}`
      : key;

    // Metni <span> içinde tut, ama JS tarafında hemen gösterme
    if (entry) {
      const textEl = document.createElement("span");
      textEl.className   = "mood-text";
      textEl.textContent = entry.moods.join("\n");
      cell.appendChild(textEl);
    }

    container.appendChild(cell);
  }
}

document.addEventListener("DOMContentLoaded", renderMonthlyHeatmap);


document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("heatmapChart");

  // 1) Hücre tıklanınca overlay oluşturma
  container.addEventListener("click", (e) => {
    if (!e.target.classList.contains("heat-cell")) return;

    const overlay = document.createElement("div");
    overlay.id = "heatmapOverlay";

    const closeBtn = document.createElement("button");
    closeBtn.className = "close-btn";
    closeBtn.textContent = "\u00D7"; // × işareti
    overlay.appendChild(closeBtn);

    // Tıklanan hücreyi klonla ve sınıf ekle
    const bigCell = e.target.cloneNode(true);
    bigCell.classList.add("active-big-cell");
    overlay.appendChild(bigCell);

    document.body.appendChild(overlay);

    // Animasyonla büyüt
    bigCell.style.transform = "scale(0)";
    bigCell.style.opacity = "0";
    bigCell.style.transition = "transform 0.25s ease, opacity 0.25s ease";

    setTimeout(() => {
      bigCell.style.transform = "scale(1)";
      bigCell.style.opacity = "1";
    }, 10);
  });

  // 2) Kapat butonuna tıklandığında animasyonlu kapatma
  document.body.addEventListener("click", (e) => {
    if (!e.target.classList.contains("close-btn")) return;

    const overlay = document.getElementById("heatmapOverlay");
    if (!overlay) return;

    const bigCell = overlay.querySelector(".active-big-cell");
    if (!bigCell) return;

    // Animasyon sınıflarını ekle
    overlay.classList.add("fade-out");
    bigCell.classList.add("scale-out");

    // DOM'dan kaldır
    setTimeout(() => {
      overlay.remove();
    }, 250); // animasyon süresi + tampon
  });
});

