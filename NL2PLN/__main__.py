import argparse
import json
from NL2PLN.utils.common import create_completion, set_model_provider, convert_logic_simple, convert_to_english
from NL2PLN.utils.prompts import nl2pln, pln2nl
from NL2PLN.metta.metta_handler import MeTTaHandler
from NL2PLN.utils.ragclass import RAG
import os
import cmd

class KBShell(cmd.Cmd):
    intro = 'Welcome to the Knowledge Base shell. Type help or ? to list commands.\n'
    prompt = 'KB> '

    def __init__(self, kb_file: str | None = None, collection_name: str = "default"):
        super().__init__()
        self.debug = False
        self.llm = False
        self.inference = False # Whether to convert inferences to natural language
        if kb_file:
            self.metta_handler = MeTTaHandler(kb_file, read_only=True)
            self.metta_handler.load_kb_from_file()
            print(f"Loaded knowledge base from {kb_file}")
        else:
            self.metta_handler = MeTTaHandler("", read_only=True)
            print("No knowledge base file specified, starting with empty KB")
        self.rag = RAG(collection_name=collection_name)
        self.query_rag = RAG(collection_name=f"{collection_name}_query", reset_db=True)
        self.conversation_history = []
        print("Type 'exit' to quit")

    def default(self, line: str):
        """Handle any input that isn't a specific command"""
        self.process_input(line)

    def do_exit(self, arg):
        """Exit the shell"""
        return True

    def do_debug(self, arg):
        """Toggle debug mode"""
        self.debug = not self.debug
        print(f"Debug mode: {'on' if self.debug else 'off'}")

    def do_inference(self, arg):
        """Toggle inference mode"""
        self.inference = not self.inference
        print(f"Inference mode: {'on' if self.inference else 'off'}")

    def do_llm(self, arg):
        """Toggle debug mode"""
        self.llm = not self.llm
        print(f"LLM mode: {'on' if self.llm else 'off'}")

    def do_provider(self, arg):
        """Set the model provider to either anthropic or openai"""
        if arg.lower() in ["anthropic", "openai"]:
            set_model_provider(arg)
            print(f"Provider: {arg}")
        else:
            print(f"Provider not recognized, defaulting to 'anthropic'")
            set_model_provider("anthropic")

    def do_demo1(self, arg):
        """Run the surgeon riddle example"""
        # First process the riddle statement
        riddle = "The surgeon who is the boys father says: 'I can't operate on him he is my son'"
        print(f"\nProcessing riddle statement:\n {riddle}")
        self.process_input(riddle)

        # Then process the follow-up question
        question = "Who is the surgeon to the son?"
        print(f"\nProcessing follow-up question:\n {question}")
        llmtmp = self.llm
        self.llm = True
        self.process_input(question)
        self.llm = llmtmp

    def do_demo2(self, arg):
        """Run a simple proof example with family relationships"""
        print("\n=== Family Relationship Proof Example ===")

        # Add basic facts
        print("\nAdding facts:")
        facts = [
            "A mother of someone is a parent of that person.",
            "A father of someone is a parent of that person.",
            "John is the father of Mary.",
            "Mary is the mother of Bob.",
            "A parent of a parent of someone is a grandparent of that person.",
        ]
        for fact in facts:
            print(f"\nProcessing: {fact}")
            self.process_input(fact)

        # Ask about the relationship
        question = "Who is John to Bob?"
        print(f"\nQuerying: {question}")
        self.process_input(question)

    def get_similar_examples(self, input_text):
        # Get examples from both RAG databases
        base_similar = self.rag.search_similar(input_text, limit=3)
        query_similar = self.query_rag.search_similar(input_text, limit=2)

        # Combine results
        similar = base_similar + query_similar

        return [
            f"Sentence: {item['sentence']}\n"
            f"From Context:\n{'\n'.join(item.get('from_context', []))}\n"
            f"Type Definitions:\n{'\n'.join(item.get('type_definitions', []))}\n"
            f"Statements:\n{'\n'.join(item.get('statements', []))}"
            for item in similar if 'sentence' in item
        ]

    def get_llm_response(self, user_input: str) -> str:
        """Get response from LLM considering conversation history"""
        messages = []
        # Add conversation history
        for msg in self.conversation_history:
            messages.append({"role": "user", "content": msg["user"]})
            if msg.get("assistant"):
                messages.append({"role": "assistant", "content": msg["assistant"]})

        # Add current input
        messages.append({"role": "user", "content": user_input})

        # Get LLM response
        response = create_completion("", messages) # System message is empty
        return response

    def process_input(self, user_input: str):
        #try:
        # Get LLM response first
        if (self.llm):
            print("\n=== LLM Response ===")
            llm_response = self.get_llm_response(user_input)
            print(llm_response)

            # Update conversation history
            self.conversation_history.append({
                "user": user_input,
                "assistant": llm_response
            })
        else:
            self.conversation_history.append({
                "user": user_input,
            })

        print("\n=== System Response ===")
        if self.debug: print(f"Processing input: {user_input}")
        similar_examples = self.get_similar_examples(user_input)
        if self.debug: print(f"Similar examples:\n{similar_examples}")
        pln_data = convert_logic_simple(user_input, nl2pln, similar_examples)
        if self.debug:
            print("\nConverted PLN data:")
            print(json.dumps(pln_data, indent=2))

        if pln_data == "Performative":
            print("This is a performative statement, not a query or statement.")
            return


        if pln_data["statements"]:
            print("Processing as statement (forward chaining)")
            fc_results = []
            # Store pln in query RAG
            self.query_rag.store_embedding({
                "sentence": user_input,
                "statements": pln_data["statements"],
                "type_definitions": pln_data.get("type_definitions", []),
                "from_context": pln_data["from_context"],
            })
            for statement in pln_data["statements"]:
                print("Got statement: " + statement)
                result = self.metta_handler.add_atom_and_run_fc(statement)
                if result:
                    fc_results.extend(result)

            if self.debug: print(f"FC results: {fc_results}")

            if self.inference:
                if fc_results:
                    print("\nInferred results:")
                    for result in fc_results:
                        english = convert_to_english(result, "", similar_examples)
                        print(f"- {result} => {english}")
                else:
                    print("No new inferences made.")

        if pln_data["questions"]:
            print("Processing as query (backward chaining)")
            metta_results = self.metta_handler.bc(pln_data["questions"][0])[0]
            if self.debug: print("metta_results: " + str(metta_results))
            for result in metta_results:
                if result:
                    english = convert_to_english(result, user_input, similar_examples)
                    print(f"- {result} => {english}\n")
                else:
                    print("Can't prove the query.")


            #except Exception as e:
            #    print(f"Error processing input: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Interactive shell for querying the knowledge base.")
    parser.add_argument("--kb-file", help="Path to the knowledge base file (.metta)", default=None)
    args = parser.parse_args()

    if args.kb_file:
        collection_name = os.path.splitext(os.path.splitext(os.path.basename(args.kb_file))[0])[0]
    else:
        collection_name = "default"

    KBShell(args.kb_file, f"{collection_name}_pln").cmdloop()

if __name__ == "__main__":
    main()
