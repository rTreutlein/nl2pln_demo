from hyperon import MeTTa
import random
import string
import os
from typing import List

class MeTTaHandler:                                                          
    def __init__(self, file: str, read_only: bool = False):
        self.metta = MeTTa()
        self.file = file
        self._read_only = read_only
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.run("!(bind! &kb (new-space))")
        self.run_metta_from_file(os.path.join(script_dir, 'chainer.metta'))
        self.run_metta_from_file(os.path.join(script_dir, 'rules.metta'))

    def run_metta_from_file(self, file_path):                                
        with open(file_path, 'r') as file:                                   
            chainerstringhere = file.read()                                  
            self.metta.run(chainerstringhere)                                
                                                                             
    @staticmethod                                                            
    def generate_random_identifier(length=8):                                
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))                                                                   
                                                                             
    @property
    def read_only(self) -> bool:
        return self._read_only

    def add_atom_and_run_fc(self, atom: str) -> List[str]:
        self.metta.run(f'!(add-atom &kb {atom})')                  
        res = self.metta.run(f'!(fc &kb {atom})')
        out = [str(elem) for elem in res[0]]               
        if not self.read_only:
            self.append_to_file(f"{atom}")
            [self.append_to_file(elem) for elem in out]
        return out

    def bc(self, atom: str) -> List[str]:
        return self.metta.run('!(ddbc &kb ' + atom + ')')

    def add_to_context(self, atom: str) -> str | None:
        """Add atom to context if no conflict exists.
        
        Returns:
            None if atom was added successfully
            The conflicting atom string if a conflict was found
        """
        exp = self.metta.parse_single(atom)
        inctx = self.metta.run("!(match &kb (: " + str(exp.get_children()[1]) + " $a) $a)")
        
        if len(inctx[0]) == 0:
            self.metta.run("!(add-atom &kb " + atom + ")")
            return None
            
        existing_atom = str(inctx[0][0])
        if str(exp.get_children()[2]) == existing_atom:
            return None
        else:
            return existing_atom

        
    def run(self, atom: str):
        return self.metta.run(atom)
                                                                             
    def store_kb_to_file(self):
        if self.read_only:
            print("Warning: Cannot store KB in read-only mode")
            return
        kb_content = self.metta.run('!(match &kb $a $a)')
        with open(self.file, 'w') as f:                                       
            for element in kb_content[0]:
                f.write(str(element) + "\n")
                                                                             
    def load_kb_from_file(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:                                       
                for elment in f:
                    self.metta.run(f'!(add-atom &kb {elment})')
        else:
            print(f"Warning: File {self.file} does not exist. No KB loaded.")

    def append_to_file(self, elem: str):
        if self.read_only:
            print("Warning: Cannot append to file in read-only mode")
            return
        with open(self.file, 'a') as f:
            f.write(elem)

if __name__ == "__main__":
    handler = MeTTaHandler('kb_backup.json')
    with open('kb_backup.json', 'w') as f:
        f.write("")

    print("\nTesting add_atom_and_run_fc:")
    
    # Test 1: Adding a new atom and running forward chaining
    atom1 = "(: ab (-> (: $a (PredicateNode A)) (PredicateNode B)))"
    print(f"Adding atom and running fc: {atom1}")
    result = handler.add_atom_and_run_fc(atom1)
    print(f"Forward chaining results: {result}")

    # Test 2: Adding another atom to trigger more inferences
    atom2 = "(: a (PredicateNode A))"
    print(f"\nAdding second atom: {atom2}")
    result = handler.add_atom_and_run_fc(atom2)
    print(f"Forward chaining results: {result}")

    print("\nTesting add_to_context:")
    
    # Test 1: Adding a new atom (should succeed)
    atom3 = "(: test1 (ImplicationLink (PredicateNode X) (PredicateNode Y)))"
    result = handler.add_to_context(atom3)
    print(f"Adding {atom3}")
    print(f"Result: {result}")  # Should print None
    
    # Test 2: Adding conflicting atom (should return existing atom)
    atom4 = "(: test1 (ImplicationLink (PredicateNode X) (PredicateNode Z)))"
    print(f"\nAdding conflicting atom: {atom4}")
    result = handler.add_to_context(atom4)
    print(f"Result: {result}")  # Should print the existing atom
    
    # Verify final context state
    print("\nTesting store_kb_to_file and load_kb_from_file:")
    
    # Store the KB to file
    print("Storing KB to file...")
    handler.store_kb_to_file()
    
    # Create a new handler instance
    print("Creating new handler and loading KB...")
    new_handler = MeTTaHandler('kb_backup.json')
    new_handler.load_kb_from_file()
    
    # Verify the loaded KB
    print("\nVerifying loaded KB contents:")
    loaded_context = new_handler.run("!(match &kb $a $b)")
    print("Loaded KB contents:", loaded_context[0])
    
    # Clean up test file
    if os.path.exists('kb_backup.json'):
        os.remove('kb_backup.json')
