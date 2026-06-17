console.log("=================================");
console.log(" DevLys Clipboard Converter ");
console.log("=================================");
console.log("Running in background...");
console.log("Press CTRL + Q to exit.");
console.log("");

const { execFile } = require("child_process");
const readline = require("readline");

const powershellPath = process.env.SystemRoot
    ? `${process.env.SystemRoot}\\System32\\WindowsPowerShell\\v1.0\\powershell.exe`
    : "powershell.exe";

function runPowerShell(command, input = "") {
    return new Promise((resolve, reject) => {
        const child = execFile(
            powershellPath,
            ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
            {
                encoding: "utf8",
                windowsHide: true,
                maxBuffer: 1024 * 1024 * 10
            },
            (error, stdout, stderr) => {
                if (error) {
                    error.message += stderr ? `\n${stderr}` : "";
                    reject(error);
                    return;
                }

                resolve(stdout);
            }
        );

        child.stdin.end(input, "utf8");
    });
}

const clipboard = {
    read: async () => runPowerShell(
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); Get-Clipboard -Raw"
    ),
    write: async text => runPowerShell(
        "[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false); $text = [Console]::In.ReadToEnd(); Set-Clipboard -Value $text",
        text
    )
};

// EXIT SHORTCUT
readline.emitKeypressEvents(process.stdin);

if (process.stdin.isTTY) {
    process.stdin.setRawMode(true);
}

process.stdin.on("keypress", (str, key) => {
    if (key.ctrl && key.name === "q") {
        console.log("\nExiting converter...");
        process.exit();
    }
});

function unicodeToDevlys(text)
{

var array_one = new Array( 
"‘",   "’",   "“",   "”",   "(",    ")",   "{",    "}",   "=", "।",  "?",  "-",  "µ", "॰", ",", ".", "् ", 
"०",  "१",  "२",  "३",     "४",   "५",  "६",   "७",   "८",   "९", "x", 

"फ़्",  "क़",  "ख़",  "ग़", "ज़्", "ज़",  "ड़",  "ढ़",   "फ़",  "य़",  "ऱ",  "ऩ",
"त्त्",   "त्त",     "क्त",  "दृ",  "कृ",

"ह्न",  "ह्य",  "हृ",  "ह्म",  "ह्र",  "ह्",   "द्द",  "क्ष्", "क्ष", "त्र्", "त्र","ज्ञ",
"छ्य",  "ट्य",  "ठ्य",  "ड्य",  "ढ्य", "द्य","द्व",
"श्र",  "ट्र",    "ड्र",    "ढ्र",    "छ्र",   "क्र",  "फ्र",  "द्र",   "प्र",   "ग्र", "रु",  "रू",
"्र",

"ओ",  "औ",  "आ",   "अ",   "ई",   "इ",  "उ",   "ऊ",  "ऐ",  "ए", "ऋ",

"क्",  "क",  "क्क",  "ख्",   "ख",    "ग्",   "ग",  "घ्",  "घ",    "ङ",
"चै",   "च्",   "च",   "छ",  "ज्", "ज",   "झ्",  "झ",   "ञ",

"ट्ट",   "ट्ठ",   "ट",   "ठ",   "ड्ड",   "ड्ढ",  "ड",   "ढ",  "ण्", "ण",  
"त्",  "त",  "थ्", "थ",  "द्ध",  "द", "ध्", "ध",  "न्",  "न",  

"प्",  "प",  "फ्", "फ",  "ब्",  "ब", "भ्",  "भ",  "म्",  "म",
"य्",  "य",  "र",  "ल्", "ल",  "ळ",  "व्",  "व", 
"श्", "श",  "ष्", "ष",  "स्",   "स",   "ह",     

"ऑ",   "ॉ",  "ो",   "ौ",   "ा",   "ी",   "ु",   "ू",   "ृ",   "े",   "ै",
"ं",   "ँ",   "ः",   "ॅ",    "ऽ",  "् ", "्" )

var array_two = new Array( 

"^", "*",  "Þ", "ß", "¼", "½", "¿", "À", "¾", "A", "\\", "&", "&", "Œ", "]","-","~ ", 
"å",  "ƒ",  "„",   "…",   "†",   "‡",   "ˆ",   "‰",   "Š",   "‹","Û",

"¶",   "d",    "[k",  "x",  "T",  "t",   "M+", "<+", "Q",  ";",    "j",   "u",
"Ù",   "Ùk",   "ä",    "–",   "—",       

"à",   "á",    "â",   "ã",   "ºz",  "º",   "í", "{", "{k",  "«", "=","K", 
"Nî",   "Vî",    "Bî",   "Mî",   "<î", "|","}",
"J",   "Vª",   "Mª",  "<ªª",  "Nª",   "Ø",  "Ý",   "æ", "ç", "xz", "#", ":",
"z",

"vks",  "vkS",  "vk",    "v",   "bZ",  "b",  "m",  "Å",  ",s",  ",",   "_",

"D",  "d",    "ô",     "[",     "[k",    "X",   "x",  "?",    "?k",   "³", 
"pkS",  "P",    "p",  "N",   "T",    "t",   "÷",  ">",   "¥",

"ê",      "ë",      "V",  "B",   "ì",       "ï",     "M",  "<",  ".", ".k",   
"R",  "r",   "F", "Fk",  ")",    "n", "/",  "/k",  "U", "u",   

"I",  "i",   "¶", "Q",   "C",  "c",  "H",  "Hk", "E",   "e",
"¸",   ";",    "j",  "Y",   "y",  "G",  "O",  "o",
"'", "'k",  "\"", "\"k", "L",   "l",   "g",      

"v‚",    "‚",    "ks",   "kS",   "k",     "h",    "q",   "w",   "`",    "s",    "S",
"a",    "¡",    "%",     "W",   "·",   "~ ", "~")

var array_one_length = array_one.length ;
var modified_substring = text;

var text_size = text.length;
var processed_text = '';

var sthiti1 = 0;
var sthiti2 = 0;
var chale_chalo = 1;

var max_text_size = 6000;

while (chale_chalo == 1)
{
    sthiti1 = sthiti2;

    if (sthiti2 < (text_size - max_text_size))
    {
        sthiti2 += max_text_size;

        while (text.charAt(sthiti2) != ' ')
        {
            sthiti2--;
        }
    }
    else
    {
        sthiti2 = text_size;
        chale_chalo = 0;
    }

    modified_substring = text.substring(sthiti1, sthiti2);

    Replace_Symbols();

    processed_text += modified_substring;
}

function Replace_Symbols()
{
    if (modified_substring != "")
    {

modified_substring = modified_substring.replace(/क़/g, "क़");
modified_substring = modified_substring.replace(/ख़‌/g, "ख़");
modified_substring = modified_substring.replace(/ग़/g, "ग़");
modified_substring = modified_substring.replace(/ज़/g, "ज़");
modified_substring = modified_substring.replace(/ड़/g, "ड़");
modified_substring = modified_substring.replace(/ढ़/g, "ढ़");
modified_substring = modified_substring.replace(/ऩ/g, "ऩ");
modified_substring = modified_substring.replace(/फ़/g, "फ़");
modified_substring = modified_substring.replace(/य़/g, "य़");
modified_substring = modified_substring.replace(/ऱ/g, "ऱ");

var position_of_f = modified_substring.indexOf("ि");

while (position_of_f != -1)
{
    var character_left_to_f = modified_substring.charAt(position_of_f - 1);

    modified_substring = modified_substring.replace(
        character_left_to_f + "ि",
        "f" + character_left_to_f
    );

    position_of_f = position_of_f - 1;

    while (
        (modified_substring.charAt(position_of_f - 1) == "्")
        &&
        (position_of_f != 0)
    )
    {
        var string_to_be_replaced =
            modified_substring.charAt(position_of_f - 2) + "्";

        modified_substring = modified_substring.replace(
            string_to_be_replaced + "f",
            "f" + string_to_be_replaced
        );

        position_of_f = position_of_f - 2;
    }

    position_of_f = modified_substring.search(/ि/, position_of_f + 1);
}

set_of_matras = "ािीुूृेैोौं:ँॅ";

modified_substring += '  ';

var position_of_half_R = modified_substring.indexOf("र्");

while (position_of_half_R > 0)
{
    var probable_position_of_Z = position_of_half_R + 2;

    var character_right_to_probable_position_of_Z =
        modified_substring.charAt(probable_position_of_Z + 1);

    while (
        set_of_matras.indexOf(character_right_to_probable_position_of_Z) != -1
    )
    {
        probable_position_of_Z++;

        character_right_to_probable_position_of_Z =
            modified_substring.charAt(probable_position_of_Z + 1);
    }

    string_to_be_replaced =
        modified_substring.substr(
            position_of_half_R + 2,
            (probable_position_of_Z - position_of_half_R - 1)
        );

    modified_substring = modified_substring.replace(
            "र्" + string_to_be_replaced,
            string_to_be_replaced + "Z"
        );

        position_of_half_R = modified_substring.indexOf("र्");
    }

    modified_substring =
        modified_substring.substr(0, modified_substring.length - 2);

    for (input_symbol_idx = 0;
         input_symbol_idx < array_one_length;
         input_symbol_idx++)
    {
        idx = 0;

        while (idx != -1)
        {
            modified_substring = modified_substring.replace(
                array_one[input_symbol_idx],
                array_two[input_symbol_idx]
            );

            idx = modified_substring.indexOf(array_one[input_symbol_idx]);
        }
    }

    }
}

return processed_text;
}

function startWatcher() {

    let lastText = "";

    console.log("Watching clipboard...");

    setInterval(async () => {

        try {

            const current = await clipboard.read();

            if (current !== lastText) {

                const hasHindi = /[\u0900-\u097F]/.test(current);

                if (hasHindi) {

                    const converted = unicodeToDevlys(current);

                    await clipboard.write(converted);

                    console.log("\n=================================");
                    console.log("Converted Successfully");
                    console.log("=================================");
                    console.log(current);
                    console.log("↓");
                    console.log(converted);
                    console.log("");
                }

                lastText = current;
            }

        } catch (err) {

            console.log("\nERROR:");
            console.log(err);

        }

    }, 1000);
}

startWatcher();
