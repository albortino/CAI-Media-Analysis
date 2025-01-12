from datetime import datetime
import ollama
import json, re
from pydantic import BaseModel, validator, ValidationError


class OllamaHandler:
    def __init__(self, model_name: str, system_prompt: str = "", debug: bool = False):
        self.debug = debug
        self.model = model_name
        self.ollama = ollama
        self.system_prompt = system_prompt if system_prompt != "" else "You are a trustworthy large language model"

    def get_response(self, prompt: str, system: str = "") -> str:
        if system == "":
            system = self.system_prompt

        response = self.ollama.generate(
            model=self.model, system=system, prompt=prompt)
        
        return response["response"]
    
class OllamaMediaAnalysis(OllamaHandler):
    def __init__(self, model_name: str, system_prompt: str = "", debug: bool = False):
        super().__init__(model_name, system_prompt, debug)
        
        
    def generate_short_summary(self, text: str, boost:str= "") -> str:
        print(f"{datetime.now().strftime('%H:%M:%S')}\t Generating short summary") if self.debug else None

        ERROR_MSG_SENTENCE = "The summary must be exactly one sentence"
        
        class ShortSummary(BaseModel):
            short_summary: str

            @validator("short_summary")
            def must_be_one_sentence(cls, value):
                # Regex for a single sentence (ending with a punctuation mark)
                if not re.match(r"^[A-Z].*[.!?]$", value.strip()):
                    raise ValueError(f"{ERROR_MSG_SENTENCE}.")
                if value.count('.') + value.count('!') + value.count('?') > 1:
                    raise ValueError(f"{ERROR_MSG_SENTENCE}.")
                return value
    
        prompt = f"Please summarize the article very concisely. First, reason about it. Finally, respond with exactly one sentence that starts with 'The article is about...'. Here is the article: <{text}>"
        response = ollama.generate(
            model=self.model, system=self.system_prompt, prompt=boost + prompt, format=ShortSummary.model_json_schema())
        
        # Validate the response       
        try:
            validated_response = ShortSummary(short_summary=response["response"])
            return validated_response.short_summary
        
        except ValidationError as e:
            print(f"Validation Error: {e}")
            
            # Retry with a boosted prompt if validation fails and no boost was tried before
            if boost == "":
                return self.generate_short_summary(
                    text=response["response"].split("short_summary")[1],
                    boost=f"{ERROR_MSG_SENTENCE}, but your answer contains more than one sentence - fix this! ",
                )
            else:
                value = response["response"].split("short_summary")[1]
                
                return response["response"] if value is None else value.strip()
    

    def generate_summary(self, text: str, boost:str = "") -> str:
        print(f"{datetime.now().strftime('%H:%M:%S')}\t Generating summary") if self.debug else None
        
        ERROR_MSG_BULLETS = "The summary must contain at least one numbered bullet point (e.g., '1. answer\n2. answer\n3. answer')"
        
        def format_bullet_points(text: str) -> str:
            """Ensure each numbered bullet point (e.g., '1.', '2.') starts with a newline character."""
            # Add a newline before bullet points if missing
            formatted_text = re.sub(r"(?<!\n)(\d\.)", r"\n\1", text)
            formatted_text = formatted_text.replace("\n\n", "\n").strip()
            
            return formatted_text
    
        class Summary(BaseModel):
            summary: str

            @validator("summary")
            def must_include_numbered_bullet_points(cls, value):
                # Ensure the summary contains at least one numbered bullet point
                if not re.search(r"\d\.", value):
                    raise ValueError(f"{ERROR_MSG_BULLETS}.")
                return value
    
        prompt = f"Your task is to briefly summarize the article. Focus on opportunities and risks, whether AI will replace or complement jobs and whether AI is experiences as machine- or human-like. Provide at maximum 7 numberd bullet points. Ensure each numbered bullet point (e.g., '1.', '2.') starts with a newline character. Here is the article: <{text}>"
        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=boost+prompt)

        # Validate and format the response
        try:
            validated_response = Summary(summary=response["response"])
            # Format bullet points to ensure they start with \n
            formatted_summary = format_bullet_points(validated_response.summary)
            return formatted_summary
        except ValidationError as e:
            print(f"Validation Error: {e}")
            # Retry with a boosted prompt if validation fails and no boost was tried before
            if boost == "":
                return self.generate_summary(
                    text=text,
                    boost=f"{ERROR_MSG_BULLETS}. Fix it for the next time! ",
                )
            else:
                formatted_summary = format_bullet_points(response["response"])
                summary_only = formatted_summary.split("summary")[1]
                return formatted_summary if summary_only is None else summary_only.strip()
            
    def answer_question(self, text: str, question: str, multiple_articles: bool = False) -> dict:
        print(f"{datetime.now().strftime('%H:%M:%S')}\t Answering question <{question[:30]}...>") if self.debug else None

        class Answer(BaseModel):
            question: str
            reasoning: str
            answer: str

        if not multiple_articles:
            prompt = f"Answer the following question based on the article provided. In your final answer highlight examples from the text. Be concise, answer in simple language and only mention topics that occured in the article and convey the opinion of the author. Here is the text: <{text}>. Question: <{question}>"

        else:
            prompt = f"Answer the following question based on the articles provided. The articles are based on the json file where the keys are the titles and the content the value.. In your final answer highlight examples from the text. Be concise, answer in simple language and only mention topics that occured in the articles and convey the opinion of the authors. Here is the text: <{text}>. Question: <{question}>"

        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=prompt,  format=Answer.model_json_schema())

        return json.loads(response["response"])

    def analyze_sentiment(self, text: str) -> dict:
        print(f"{datetime.now().strftime('%H:%M:%S')}\t Analyzing sentiment") if self.debug else None

        class Sentiment(BaseModel):
            sentiment_reason: str
            sentiment_value: int

        prompt = f"Your task is to analyze the sentiment of the following text. In the first step, you have to thoroughly think about the answer. Finally, provide a single integer number between -5 and +5 . -5 means very negative towards AI, highlighting risks and limitations of AI; 0 is neutral towards AI; +5 is extremely positive towards AI, mainly writing about opportunities and potentials to exploit. Here is the article: <{text}>"
        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=prompt,  format=Sentiment.model_json_schema())

        response = json.loads(response["response"])
        
        if response.get("sentiment_value") > 5 and response.get("sentiment_value")/10 > -5:
            response["sentiment_value"] = response.get("sentiment_value")/10
            
        return response

    def extract_topics(self, text: str) -> list:

        class Topics(BaseModel):
            topics: list[str]

        prompt = f"Your task is to create a **list of strings** with all perspectives and aspects of the topic Artifical Intelligence that were are being widely covered in the following article. Every topic should be at maximum two words long. Here is the article: <{text}>"
        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=prompt,  format=Topics.model_json_schema())

        cleaned_topic_list = [topic for topic in json.loads(response["response"]).get(
            "topics") if len(topic.split(" ")) < 3 and len(topic) > 2]

        return cleaned_topic_list

    def create_topic_clusters(self, topics: list) -> dict:

        class TopicClusters(BaseModel):
            cluster: dict[str, list[str]]

        prompt = f"Please cluster the following topics into groups with similar meaning. Give every cluster a name that summarizes its content. Answer in the form of a dictionary with 'cluster name: all topics within in the cluster'. Here are the values for classification <{', '.join(topics)}>"
        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=prompt,  format=TopicClusters.model_json_schema())

        return json.loads(response["response"]).get("cluster")


if __name__ == "__main__":
    model = ollama.list().get("models")[0].get("model")
    llm = OllamaHandler(model_name=model)
    print(llm.get_response("Say hello!"))