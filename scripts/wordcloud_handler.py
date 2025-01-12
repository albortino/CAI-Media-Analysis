import spacy, matplotlib.pyplot as plt, os
from wordcloud import WordCloud
from collections import Counter

class WordCloudHandler:
    def __init__(self, spacy_model: str = "en_core_web_sm", width: int = 800, height: int = 400, background_color: str = "white"):
        
        self.spacy_model = spacy_model      
        self.WordCloud = WordCloud(width=width,
            height=height,
            background_color=background_color,
            min_font_size=10,
            max_font_size=150,
            random_state=42)   
    def set_parameter(self, parameter: str, value):
        ''' Sets parameter of WordCloud object'''
        setattr(self.WordCloud, parameter, value)
    
    def set_height(self, new_heigth: int):
        self.height = new_heigth
    
    def get_cleaned_words(self, text_list: list, min_occurence=3) -> list:
        # Load spacy model
        nlp = spacy.load(self.spacy_model)
        
        # Combine all strings into one text
        text = " ".join(text_list)
        text.replace("\n", " ")
        
        # Process the text with spacy
        doc = nlp(text)
        
        # Get non-stop words
        words = [token.text for token in doc if not token.is_stop and token.is_alpha and token.text != " " and token.text != "\n"]
        
        # Remove words that occur less than min_occurence times
        words = [word for word in words if words.count(word) >= min_occurence]
        
        return words
        
        
    def generate_word_cloud(self, text_list: list, output_path:str = None, wordcloud_name: str = "WordCloud") -> Counter:
    
       # Get clean text without stopwords etc.
        words = self.get_cleaned_words(text_list)
        processed_text = " ".join(words)
        
        # Create and generate a word cloud image
        self.WordCloud.generate(processed_text)
        
        # Display the word cloud
        plt.figure(figsize=(10, 5))
        plt.imshow(self.WordCloud, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        
        if output_path:
            output_path = self.export_word_cloud(plt, output_path, wordcloud_name)
        else:
            plt.show()
        
        # Return most common words and their frequencies
        word_freq = Counter(words).most_common(10)
        return word_freq, output_path
        
    
    def export_word_cloud(self, plt: plt, path, wordcloud_name: str) -> str:
        if not os.path.exists(path):
            os.makedirs(path)
            
        output_path = f"{path}/wordcloud_{wordcloud_name}.png"

        plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close()
        
        return output_path
        

    def process_wordcloud(self, input, path: str, wordcloud_name: str = None) -> dict:
        """ Iterates over each highlight color in the document and generates a word cloud for each color."""
        
        def call_generate_cloud(input: str, path: str, wordcloud_name: str) -> list:
            if not os.path.exists(path):
                print(f"Creating folder: {path}")
                os.makedirs(path)
                
            word_frequencies, output_path = self.generate_word_cloud(
                input,
                output_path=path,
                wordcloud_name=wordcloud_name
            )
            
            return word_frequencies, output_path
                
        new_wordcloud_data = {}
        
        # If input type is dict (e.g.: <highlights>) iterate over all highlighted sentences.
        # Otherwise take the list
        if isinstance(input, dict):
            for key, sentences in input.items():
                wordcloud_name = key.replace("#", "")
                word_frequencies, path = call_generate_cloud(sentences, path, wordcloud_name)
                new_wordcloud_data[wordcloud_name] = {"word_frequencies": word_frequencies, "path": path}
                
        elif isinstance(input, list):
            sentences = input
            word_frequencies, path = call_generate_cloud(sentences, path, wordcloud_name)
            new_wordcloud_data[wordcloud_name] = {"word_frequencies": word_frequencies, "path": path}

            
        return new_wordcloud_data
    
if __name__ == "__main__":
    wc = WordCloudHandler()
    wc.generate_word_cloud(["lorem", "ipsim", "dolor", "sit", "amen", "lorem"])