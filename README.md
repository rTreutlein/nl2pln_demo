
# This is a demo of the nl2pln package

Dependencies:

- ollama
 Easiest way to run ollama is to use docker:
 ``` bash
 docker run -d -p 11434:11434 --name ollama ollama/ollama
 docker exec -it ollama ollama pull nomic-embed-text
 ```
- qdrant
 Easiest way to run qdrant is to use docker:
 ``` bash
 docker run -d -p 6333:6333 qdrant/qdrant
 ```

To run the demo:

```bash
uv run python -m NL2PLN
```

Now you can enter english sentences which get converted to pln and added to the knowledge base.

If you ask a question the system will try to proof it with the contents of the knowledge base. (Proof depth is currently limited for performance reasons)

There are also 2 demos you can run with the following commands demo1 and demo2:

**demo1** demonstrates how using this system can improve upon pure language models.
by generating a simple statment + query that the llm gets wrong.

**demo2** demonstrates how we can use this system to understand the results of our query.
by generating a slightly more complex scenario and showing how the results of the query contain a full proof trace.

Other commands:

**debug**: enables debug mode which prints out more information  
**llm**: enables llm mode which also queries the llm with the same text for comparison  
**inference**: after adding new knowledge we generate inferences by forward chaining, this shows the results of the inference  
**exit**: exits the program  

