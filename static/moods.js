const moodCategories = {
    "pozitif": {
            baseColor: ["#A5D6A7", "#4CAF50", "#1B5E20"],
            moods: ["Mutlu", "Huzurlu", "Rahat", "Minnettar", "Umutlu", "Coşkulu", "İlham almış", "Sevilmiş"]
        },
        "nötr": {
            baseColor: ["#90CAF9", "#2196F3", "#0D47A1"],
            moods: ["Sıkılmış", "Boşlukta", "Kararsız", "Alakasız", "Dalgın", "Duyarsız", "Durgun", "Yorgun"]
        },
        "melankolik":{
             baseColor: ["#CE93D8", "#9C27B0", "#4A148C"],
             moods: ["Hüzünlü", "İçine kapanık", "Özlem dolu", "Yalnız", "Kırgın", "Hayal kırıklığına uğramış", "Umutsuz", "Değersiz hissetmek"]
        },
        "stresli":{
             baseColor: ["#EF9A9A", "#F44336", "#B71C1C"],
             moods: ["Endişeli", "Gergin", "Kızgın", "Kıskanç", "Suçlu", "Panik", "Bunalmış", "Gergin", "Kaygılı"]
            
        },
        "negatif":{
             baseColor: ["#FFCC80", "#FFC400", "#E68A00"],
             moods: ["Tükenmiş", "Umursamaz", "Yetersiz", "Yalnızlık içinde", "Terkedilmiş", "Çaresiz", "İnatçı", "Kapanmak isteyen"]
            
        },
        "karışık":{
             baseColor: ["#6D6D6D", "#313131", "#000000"],
             moods: ["Belirsiz", "Hem iyi hem kötü", "Tanımlanamayan", "Karmaşık", "Parçalanmış", "Belirsizlikten rahatsız"]
            
        }
    };

// Yoğunluk tonları (açık → koyu)
const intensityShades = {
    low: 0.6,   // Açık
    medium: 0.8, // Orta
    high: 1     // Orijinal renk
};

// Renk tonunu ayarlama fonksiyonu
function adjustColor(hex, factor) {
    const r = Math.min(255, Math.floor(parseInt(hex.slice(1,3), 16) * factor));
    const g = Math.min(255, Math.floor(parseInt(hex.slice(3,5), 16) * factor));
    const b = Math.min(255, Math.floor(parseInt(hex.slice(5,7), 16) * factor));
    return `rgb(${r}, ${g}, ${b})`;
}

let stepIndex = 0;
const steps = ["high", "medium", "low"];
let selectedMoods = [];

function renderStep() {
    const step = steps[stepIndex];
    const container = document.getElementById("step-container");
    container.innerHTML = `<h3>${
        step === "high" ? "Yoğun hissettiğiniz duygular" 
        : step === "medium" ? "Orta yoğunluktaki duygular" 
        : "Hafif hissettiğiniz duygular"
    }</h3>`;

    Object.entries(moodCategories).forEach(([category, data]) => {
        // Yoğunluğa göre baseColor dizisinden doğru tonu al
        let colorIndex = step === "low" ? 0 : step === "medium" ? 1 : 2;
        const color = data.baseColor[colorIndex];

        let html = `<div style="border:1px solid #ccc; margin:10px; padding:10px; background:${color};">`;
        html += `<h4>${category.toUpperCase()}</h4>`;
        
        data.moods.forEach(mood => {
            html += `
                <label style="display:block; margin:4px 0;">
                    <input type="checkbox" value="${mood}" data-intensity="${step}">
                    ${mood}
                </label>
            `;
        });

        html += `</div>`;
        container.innerHTML += html;
    });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js")
    .then(() => console.log("Service Worker kayıt edildi"))
    .catch(err => console.error("SW hatası:", err));
}
