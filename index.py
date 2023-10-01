import re
import unicodedata
from werkzeug.utils import secure_filename
import os
import base64

from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from flask import Flask, render_template, abort, request
import ulid

app = Flask(__name__)


async def image_file_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        data = base64.b64encode(image_file.read())

    return data.decode("utf-8")


@app.route("/", methods=["GET", "POST"])
async def generator():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        uid = ulid.new()
        f = request.files['file']
        f.save(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "static/" + uid.str + ".txt"
            )
        )
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "static/" + uid.str + ".txt"
            ),
            encoding="utf-8",
        ) as f:
            text = f.read().replace("\n", "").replace(" ", "")
        text = re.sub("\u3000", "", text)
        text = re.sub("・", "", text)
        text = re.sub("「", "", text)
        text = re.sub("」", "", text)
        text = re.sub("（", "", text)
        text = re.sub("）", "", text)
        text = re.sub("\n", " ", text)
        text = re.sub("\\n", "", text)
        text = re.sub("\\n", " ", text)
        t = Tokenizer()
        tokenized_text = t.tokenize(text)
        words_list = []
        for token in tokenized_text:
            tokenized_word = token.surface
            hinshi = token.part_of_speech.split(",")[0]
            hinshi2 = token.part_of_speech.split(",")[1]
            if hinshi == "名詞":
                if (hinshi2 != "数") and (hinshi2 != "代名詞") and (hinshi2 != "非自立"):
                    words_list.append(tokenized_word)
        words_wakachi = " ".join(words_list)
        font = "keifont.ttf"
        word_cloud = WordCloud(
            font_path=font,
            width=1500,
            height=900,
            min_font_size=5,
            collocations=False,
            background_color="white",
            max_words=400,
        ).generate(words_wakachi)
        figure = plt.figure(figsize=(15, 10))
        plt.imshow(word_cloud)
        plt.tick_params(labelbottom=False, labelleft=False)
        plt.xticks([])
        plt.yticks([])
        figure.savefig(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
            "static/" + uid.str + ".png",)
        )
        b64 = await image_file_to_base64(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
            "static/" + uid.str + ".png"),
        )
        # きれいにしようね (?)
        os.remove(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
            "static/" + uid.str + ".png"),
        )
        os.remove(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "static/" + uid.str + ".txt"
            )
        )
        # きれいになったね (?)
        return render_template("generated.html", b64=b64)