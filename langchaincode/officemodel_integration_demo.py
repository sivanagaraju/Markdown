#!/usr/bin/env python3
"""
Complete Integration Example: OfficeModelLangchainClient with DSPy, LangChain & LangGraph
This example demonstrates how to use the OfficeModel wrapper across different frameworks.
"""

import os
import dspy
from typing import Dict, Any, List
from datetime import datetime

# Import our custom wrappers
from OfficeModel_langchain_client import OfficeModelLangchainClient
from dspy_OfficeModel_wrapper import OfficeModelDSPyLM

# LangChain imports
try:
    from langchain.schema import HumanMessage, SystemMessage
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("LangChain not available. Install with: pip install langchain")
    LANGCHAIN_AVAILABLE = False

# LangGraph imports  
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.state import CompiledStateGraph
    from typing_extensions import TypedDict
    LANGGRAPH_AVAILABLE = True
except ImportError:
    print("LangGraph not available. Install with: pip install langgraph")
    LANGGRAPH_AVAILABLE = False


class IntegrationDemo:
    """
    Demonstration class showing integration across DSPy, LangChain, and LangGraph
    using the OfficeModelLangchainClient as the underlying LLM provider.
    """

    def __init__(self):
        """Initialize the demo with all three framework integrations."""
        self.setup_clients()

    def setup_clients(self):
        """Set up clients for all three frameworks."""
        print("🚀 Setting up OfficeModel clients for all frameworks...")

        # 1. DSPy Setup
        try:
            self.dspy_lm = OfficeModelDSPyLM(
                model_name="gemini-2.0-flash",
                temperature=0.7,
                max_tokens=150
            )
            dspy.configure(lm=self.dspy_lm)
            print("✅ DSPy client configured")
        except Exception as e:
            print(f"❌ DSPy setup failed: {e}")
            self.dspy_lm = None

        # 2. LangChain Setup
        if LANGCHAIN_AVAILABLE:
            try:
                self.langchain_lm = OfficeModelLangchainClient(
                    model_name="gemini-2.0-flash",
                    temperature=0.7,
                    max_tokens=150
                )
                print("✅ LangChain client configured")
            except Exception as e:
                print(f"❌ LangChain setup failed: {e}")
                self.langchain_lm = None
        else:
            self.langchain_lm = None

        # 3. LangGraph Setup (uses same LangChain client)
        if LANGGRAPH_AVAILABLE and self.langchain_lm:
            try:
                self.setup_langgraph()
                print("✅ LangGraph client configured")
            except Exception as e:
                print(f"❌ LangGraph setup failed: {e}")
                self.langgraph_app = None
        else:
            self.langgraph_app = None

    def setup_langgraph(self):
        """Set up a LangGraph application using OfficeModel client."""

        # Define state structure
        class AgentState(TypedDict):
            question: str
            context: str
            answer: str
            reasoning: str

        # Define nodes
        def research_node(state: AgentState) -> Dict[str, Any]:
            """Research node that gathers context."""
            question = state["question"]

            # Use OfficeModel client for research
            research_prompt = f"Provide relevant context and background information for this question: {question}"
            response = self.langchain_lm.invoke([{"role": "user", "content": research_prompt}])

            return {
                "context": response.content if hasattr(response, 'content') else str(response),
                "question": question
            }

        def reasoning_node(state: AgentState) -> Dict[str, Any]:
            """Reasoning node that analyzes the question and context."""
            question = state["question"]
            context = state.get("context", "")

            reasoning_prompt = f"""
            Question: {question}
            Context: {context}

            Provide step-by-step reasoning for how to answer this question based on the context.
            """

            response = self.langchain_lm.invoke([{"role": "user", "content": reasoning_prompt}])

            return {
                "reasoning": response.content if hasattr(response, 'content') else str(response),
                "question": question,
                "context": context
            }

        def answer_node(state: AgentState) -> Dict[str, Any]:
            """Answer node that provides the final answer."""
            question = state["question"]
            context = state.get("context", "")
            reasoning = state.get("reasoning", "")

            answer_prompt = f"""
            Question: {question}
            Context: {context}
            Reasoning: {reasoning}

            Provide a clear, concise answer to the question.
            """

            response = self.langchain_lm.invoke([{"role": "user", "content": answer_prompt}])

            return {
                "answer": response.content if hasattr(response, 'content') else str(response),
                "question": question,
                "context": context,
                "reasoning": reasoning
            }

        # Build the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("research", research_node)
        workflow.add_node("reasoning", reasoning_node)
        workflow.add_node("answer", answer_node)

        # Add edges
        workflow.set_entry_point("research")
        workflow.add_edge("research", "reasoning")
        workflow.add_edge("reasoning", "answer")
        workflow.add_edge("answer", END)

        # Compile the graph
        self.langgraph_app = workflow.compile()

    def demo_dspy(self, question: str) -> Dict[str, Any]:
        """Demonstrate DSPy functionality with OfficeModel."""
        if not self.dspy_lm:
            return {"error": "DSPy not available"}

        print(f"\n🔬 DSPy Demo: {question}")

        try:
            # Create DSPy modules
            qa = dspy.ChainOfThought("question -> answer")
            summarizer = dspy.Predict("text -> summary")

            # Get answer
            result = qa(question=question)

            # Summarize the answer
            summary = summarizer(text=result.answer)

            return {
                "framework": "DSPy",
                "question": question,
                "answer": result.answer,
                "summary": summary.summary,
                "reasoning": getattr(result, 'reasoning', 'Not available')
            }

        except Exception as e:
            return {"framework": "DSPy", "error": str(e)}

    def demo_langchain(self, question: str) -> Dict[str, Any]:
        """Demonstrate LangChain functionality with OfficeModel."""
        if not self.langchain_lm:
            return {"error": "LangChain not available"}

        print(f"\n🔗 LangChain Demo: {question}")

        try:
            # Create a simple chain
            prompt = PromptTemplate(
                input_variables=["question"],
                template="Answer this question with detailed explanation: {question}"
            )

            chain = LLMChain(llm=self.langchain_lm, prompt=prompt)
            result = chain.run(question=question)

            return {
                "framework": "LangChain",
                "question": question,
                "answer": result
            }

        except Exception as e:
            return {"framework": "LangChain", "error": str(e)}

    def demo_langgraph(self, question: str) -> Dict[str, Any]:
        """Demonstrate LangGraph functionality with OfficeModel."""
        if not self.langgraph_app:
            return {"error": "LangGraph not available"}

        print(f"\n📊 LangGraph Demo: {question}")

        try:
            # Run the graph
            result = self.langgraph_app.invoke({
                "question": question,
                "context": "",
                "answer": "",
                "reasoning": ""
            })

            return {
                "framework": "LangGraph",
                "question": question,
                "context": result.get("context", ""),
                "reasoning": result.get("reasoning", ""),
                "answer": result.get("answer", "")
            }

        except Exception as e:
            return {"framework": "LangGraph", "error": str(e)}

    def run_comprehensive_demo(self):
        """Run a comprehensive demo across all frameworks."""
        questions = [
            "What are the key benefits of using microservices architecture?",
            "How does machine learning differ from traditional programming?",
            "What are the main challenges in implementing DevOps practices?"
        ]

        print("=" * 80)
        print("🌟 COMPREHENSIVE OfficeModel INTEGRATION DEMO")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Model: Gemini-2.0-Flash via OfficeModel API")
        print("=" * 80)

        results = []

        for i, question in enumerate(questions, 1):
            print(f"\n{'='*20} QUESTION {i} {'='*20}")
            print(f"Q: {question}")

            # Test each framework
            dspy_result = self.demo_dspy(question)
            langchain_result = self.demo_langchain(question)
            langgraph_result = self.demo_langgraph(question)

            results.append({
                "question": question,
                "dspy": dspy_result,
                "langchain": langchain_result,
                "langgraph": langgraph_result
            })

        # Print summary
        print("\n" + "=" * 80)
        print("📊 DEMO SUMMARY")
        print("=" * 80)

        for framework in ["DSPy", "LangChain", "LangGraph"]:
            successful = sum(1 for r in results if not r[framework.lower()].get("error"))
            total = len(results)
            print(f"{framework}: {successful}/{total} successful")

        return results


def main():
    """Main demonstration function."""
    print("🚀 Starting OfficeModel Integration Demo...")
    print("Make sure you have set the required environment variables:")
    print("- OfficeModel_API_KEY, OfficeModel_BASE_URL, OfficeModel_USECASE_ID")
    print("- CERTS_PATH, USE_API_GATEWAY, APIGEE_OAUTH_URL")
    print("- APIGEE_CONSUMER_KEY, APIGEE_CONSUMER_SECRET")

    try:
        demo = IntegrationDemo()
        results = demo.run_comprehensive_demo()

        print("\n🎉 Demo completed successfully!")
        print("You can now use OfficeModelLangchainClient with:")
        print("✅ DSPy - for self-optimizing LLM pipelines")
        print("✅ LangChain - for rapid application development")  
        print("✅ LangGraph - for complex multi-agent workflows")

        return results

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Verify all environment variables are set correctly")
        print("2. Check network connectivity to OfficeModel API")
        print("3. Ensure SSL certificates are valid")
        print("4. Verify API credentials and permissions")
        return None


if __name__ == "__main__":
    main()
