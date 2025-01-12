from datetime import datetime
from turtle import st
import ollama
import json, re
from pydantic import BaseModel, validator, ValidationError


class OllamaHandler:
    """" Handles ollama with some extra functionalities. """
    
    def __init__(self, model_name: str, system_prompt: str = "", debug: bool = False):
        """ Initialize the OllamaHandler with model name, system prompt, and debug flag. """
    
        self.debug = debug
        self.model = model_name
        self.ollama = ollama
        self.system_prompt = system_prompt if system_prompt != "" else "You are a trustworthy large language model"

    def get_response(self, prompt: str, system: str = "") -> str:
        """ Get the response text of the ollama.response. """
        if system == "":
            system = self.system_prompt

        response = self.ollama.generate(
            model=self.model, system=system, prompt=prompt)
        
        return response["response"]
    
class OllamaMediaAnalysis(OllamaHandler):
    def __init__(self, model_name: str, system_prompt: str = "", debug: bool = False):
        """ Initialize the OllamaHandler with model name, system prompt, and debug flag. """

        super().__init__(model_name, system_prompt, debug)
        
        
    def generate_short_summary(self, text: str, boost:str= "") -> str:
        """ Returns a short summary in one word

        Args:
            text (str): Input text
            boost (str, optional): Boost string to inject error messages. Defaults to "".

        Raises:
            ValueError: If the summary is not only one sentence

        Returns:
            str: Short Summary
        """
        
        print(f"{datetime.now().strftime('%H:%M:%S')}\t Generating short summary") if self.debug else None

        ERROR_MSG_SENTENCE = "The summary must be exactly one sentence"
        
        class ShortSummary(BaseModel):
            """ Pydantic object that verifies the short summary format (one sentence). """
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
        """ Generates the summary of the input text with bullet points.

        Args:
            text (str): Input text
            boost (str, optional): Boost string to inject error messages. Defaults to "".

        Raises:
            ValueError: Is raised if summary does not contain bullet points

        Returns:
            str: Summary (with bullet points)
        """
        
        print(f"{datetime.now().strftime('%H:%M:%S')}\t Generating summary") if self.debug else None
        
        ERROR_MSG_BULLETS = ("The summary must contain at least one numbered bullet point "
                             "(e.g., '1. **headline1**: answer1\\n2 **headline2**:. answer2\\n3. **headline3**: answer3')")
        
        def ensure_numbered_list(text: str) -> str:
            """
            Ensures that the text is formatted as a numbered bullet point list.
            If no list format is detected, converts each line into a numbered item.
            """
            
            if not re.search(r"\d\.", text):
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                numbered_lines = [f"{i+1}. {line}" for i, line in enumerate(lines)]
                return "\n".join(numbered_lines)
            return text.strip()
    
    
        class Summary(BaseModel):
            """ Pydantic object that verifies the summary format (bullet points). """
            summary: str

            @validator("summary")
            def must_include_numbered_bullet_points(cls, value):
                # Ensure the summary contains at least 2 numbered bullet point
                bullet_points = re.findall(r"^\d\.", value, re.MULTILINE)
                
                if len(bullet_points) < 3:
                    raise ValueError("The summary must contain at least three numbered bullet points.")
                return value
    
        prompt = f"Your task is to briefly summarize the article. Focus on opportunities and risks, whether AI will replace or complement jobs and whether AI is experiences as machine- or human-like. Provide at maximum 7 numberd bullet points. Ensure each numbered bullet point (e.g., '1.', '2.') starts with a newline character. Here is the article: <{text}>"
        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=boost + prompt)

        # Validate and format the response
        try:
            validated_response = Summary(summary=response["response"])
            # Format bullet points to ensure they start with \n
            formatted_summary = ensure_numbered_list(validated_response.summary)
            return formatted_summary
        except ValidationError as e:
            print(f"Validation Error: {e}")
            # Retry with a boosted prompt if validation fails and no boost was tried before
            if boost == "":
                return self.generate_summary(
                    text=text,
                    boost=f"{ERROR_MSG_BULLETS}. Fix it to inlcude a valid list! ",
                )
            else:
                fallback_summary = ensure_numbered_list(response["response"])
                return fallback_summary
            
    def answer_question(self, text: str, question: str, multiple_articles: bool = False) -> dict:
        """ Answers a specific questions so that no further information has to be provided

        Args:
            text (str): Input text
            question (str): Question to answer. In case of multiple_articles==True the questions should be in JSON format.
            multiple_articles (bool, optional): Flag if the questions should be answered for one article only or several articles. Defaults to False.

        Returns:
            dict: Question, Reasoning, Answer
        """
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
        """ Analyzes the sentiment from -5 (negative), 0 (neutral), +5 (positive)

        Args:
            text (str): Input text

        Returns:
            dict: sentiment reason, sentiment value
        """
        print(f"{datetime.now().strftime('%H:%M:%S')}\t Analyzing sentiment") if self.debug else None

        class Sentiment(BaseModel):
            sentiment_reason: str
            sentiment_value: int

        prompt = f"Your task is to analyze the sentiment of the following text. In the first step, you have to thoroughly think about the answer. Finally, provide a single integer number between -5 and +5 . -5 means very negative towards AI, highlighting risks and limitations of AI; 0 is neutral towards AI; +5 is extremely positive towards AI, mainly writing about opportunities and potentials to exploit. Here is the article: <{text}>"
        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=prompt,  format=Sentiment.model_json_schema())

        response = json.loads(response["response"])
        
        """
        if response.get("sentiment_value") > 5 and response.get("sentiment_value")/10 > -5:
            response["sentiment_value"] = response.get("sentiment_value")/10"""
            
        return response

    def extract_topics(self, text: str) -> list[str]:
        """ Extracts a list of topics that are mentioned in the article.

        Args:
            text (str): Input text

        Returns:
            list[str]: List of topics (single words or short sentences)
        """

        class Topics(BaseModel):
            topics: list[str]

        prompt = f"Your task is to create a **list of strings** with all perspectives and aspects of the topic Artifical Intelligence that were are being widely covered in the following article. Every topic should be at maximum two words long. Here is the article: <{text}>"
        response = self.ollama.generate(
            model=self.model, system=self.system_prompt, prompt=prompt,  format=Topics.model_json_schema())

        cleaned_topic_list = [topic for topic in json.loads(response["response"]).get(
            "topics") if len(topic.split(" ")) < 3 and len(topic) > 2]

        return cleaned_topic_list

    def create_topic_clusters(self, topics: list[str]) -> dict[str, list[str]]:
        """ Summarizes the provided topics into clusters.
        
        Args:
            topics (list[str]): A list of topics in form of words or short sentences

        Returns:
            dict[str, list[str]]: Cluster Name: topics
        """

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