require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

const Report = mongoose.model("Report", {
    plantName: String,
    disease: String,
    image: String
});

app.post("/report", async (req, res) => {
    try {
        const data = await Report.create(req.body);
        res.json({
            message: "Report Saved",
            data
        });
    } catch (err) {
        console.error("Error creating report:", err);
        res.status(500).json({ error: "Failed to save report" });
    }
});

// Start listening first
app.listen(5000, () => {
    console.log("Server running on port 5000");
});

// Connect to MongoDB asynchronously
const mongoURI = process.env.MONGODB_URI || "mongodb+srv://dinesh:mehukon@cluster0.rksaqdu.mongodb.net/?appName=Cluster0";
console.log("Connecting to MongoDB at:", mongoURI);

mongoose.connect(mongoURI)
    .then(() => {
        console.log("MongoDB Connected Successfully");
    })
    .catch(err => {
        console.error("MongoDB Connection Error:", err);
    });