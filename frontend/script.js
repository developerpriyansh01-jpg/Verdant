// Upload Image Preview

const uploadBtn = document.querySelector(".upload-box button");
const previewImg = document.querySelector(".preview img");

const fileInput = document.createElement("input");
fileInput.type = "file";
fileInput.accept = "image/*";

uploadBtn.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) return;

    const reader = new FileReader();

    reader.onload = function (e) {
        previewImg.src = e.target.result;
    };

    reader.readAsDataURL(file);

});


// Scan Button

const scanBtn = document.querySelector(".scan-btn");

scanBtn.addEventListener("click", () => {

    if (previewImg.src.includes("plant.jpg")) {

        alert("Please upload a plant image first!");

        return;

    }

    scanBtn.innerHTML = "Scanning...";

    scanBtn.disabled = true;

    setTimeout(() => {

        document.querySelector(".result h3").innerText = "Tomato Plant";

        document.querySelector(".result p").innerText = "90% Match";

        scanBtn.innerHTML = "Scan Plant";

        scanBtn.disabled = false;

        alert("Plant scanned successfully!");

    }, 2500);

});


// Sidebar Active Menu

const menu = document.querySelectorAll(".sidebar li");

menu.forEach(item => {

    item.addEventListener("click", () => {

        menu.forEach(i => i.classList.remove("active"));

        item.classList.add("active");

    });

});


// Search Box

const search = document.querySelector(".search input");

search.addEventListener("keyup", () => {

    console.log("Searching :", search.value);

});


// Smooth Scroll

document.querySelectorAll("a").forEach(anchor => {

    anchor.addEventListener("click", function (e) {

        e.preventDefault();

        document.querySelector(this.getAttribute("href"))?.scrollIntoView({
            behavior: "smooth"
        });

    });

});