"""SNARK adapter for circom/snarkjs integration.

Provides Python wrapper for snarkjs functionality including witness generation,
proof creation, and calldata formatting for Solidity verifiers.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import env_str


class SnarkClient:
    """Real SNARK client that wraps snarkjs CLI for proof generation."""

    def __init__(self):
        # Use absolute paths to avoid working directory issues
        project_root = Path(__file__).parent.parent
        self.circuits_dir = project_root / env_str("CIRCUITS_DIR", "circuits")
        self.build_dir = self.circuits_dir / "build"
        self.wasm_path = self.build_dir / "redaction_js" / "redaction.wasm"
        self.zkey_path = self.build_dir / "redaction_final.zkey"
        self.vkey_path = self.build_dir / "verification_key.json"
        if not self.is_available():
            raise FileNotFoundError(
                "Required SNARK artifacts not found. Ensure redaction.wasm, redaction_final.zkey, "
                "and verification_key.json are present in circuits/build."
            )
        
    def is_enabled(self) -> bool:
        """Real SNARK functionality is always enabled."""
        return True
    
    def is_available(self) -> bool:
        """Check if all required circuit artifacts are available."""
        return (
            self.wasm_path.exists() and 
            self.zkey_path.exists() and 
            self.vkey_path.exists()
        )
    
    def _run_snarkjs(self, args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run snarkjs command with given arguments."""
        cmd = ["snarkjs"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.circuits_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"snarkjs command failed: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError("snarkjs not found. Please install snarkjs: npm install -g snarkjs")
    
    def generate_witness(self, public_inputs: Dict[str, Any], private_inputs: Dict[str, Any]) -> Optional[Path]:
        """Generate witness from inputs using snarkjs wtns calculate."""
        if not self.is_available():
            raise RuntimeError("SNARK artifacts missing; cannot generate witness")
            
        # Combine all inputs
        inputs = {**public_inputs, **private_inputs}
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(inputs, f, indent=2)
            input_path = Path(f.name)
        
        try:
            # Generate witness
            witness_path = self.build_dir / "witness.wtns"
            self._run_snarkjs([
                "wtns", "calculate",
                str(self.wasm_path),
                str(input_path),
                str(witness_path)
            ])
            
            return witness_path if witness_path.exists() else None
            
        finally:
            # Clean up temp file
            input_path.unlink(missing_ok=True)
    
    def prove(self, witness_path: Path) -> Optional[Tuple[Dict[str, Any], List[str]]]:
        """Generate Groth16 proof from witness."""
        if not witness_path.exists():
            raise RuntimeError("Witness file not found for Groth16 proof generation")
            
        proof_path = self.build_dir / "proof.json"
        public_path = self.build_dir / "public.json"
        
        try:
            # Generate proof
            self._run_snarkjs([
                "groth16", "prove",
                str(self.zkey_path),
                str(witness_path),
                str(proof_path),
                str(public_path)
            ])
            
            if not (proof_path.exists() and public_path.exists()):
                return None
                
            # Load results
            with open(proof_path, 'r') as f:
                proof = json.load(f)
            with open(public_path, 'r') as f:
                public_signals = json.load(f)
                
            return proof, public_signals
            
        except Exception:
            return None
    
    def verify_proof(self, proof: Dict[str, Any], public_signals: List[str]) -> bool:
        """Verify proof using snarkjs groth16 verify."""
        if not self.is_available():
            raise RuntimeError("SNARK artifacts missing; cannot verify proof")
            
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(proof, f)
            proof_path = Path(f.name)
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(public_signals, f)
            public_path = Path(f.name)
        
        try:
            # Verify proof
            result = self._run_snarkjs([
                "groth16", "verify",
                str(self.vkey_path),
                str(public_path),
                str(proof_path)
            ])
            
            return "OK!" in result.stdout
            
        except Exception:
            return False
        finally:
            # Clean up temp files
            proof_path.unlink(missing_ok=True)
            public_path.unlink(missing_ok=True)
    
    def format_calldata(self, proof: Dict[str, Any], public_signals: List[str]) -> Optional[Tuple[List[int], List[List[int]], List[int], List[int]]]:
        """Format proof and public signals for Solidity verifier calldata."""
        if not proof or not public_signals:
            return None
            
        try:
            # Parse proof components
            pi_a = proof.get("pi_a", [])
            pi_b = proof.get("pi_b", [])
            pi_c = proof.get("pi_c", [])
            
            if not (isinstance(pi_a, list) and isinstance(pi_b, list) and isinstance(pi_c, list)):
                return None
                
            # Convert to integers and format for Solidity
            # pA: [pi_a[0], pi_a[1]] (drop the third coordinate which is always 1)
            pA = [int(pi_a[0]), int(pi_a[1])]
            
            # pB: [[pi_b[0][1], pi_b[0][0]], [pi_b[1][1], pi_b[1][0]]] (swap G2 limbs)
            pB = [
                [int(pi_b[0][1]), int(pi_b[0][0])],
                [int(pi_b[1][1]), int(pi_b[1][0])]
            ]
            
            # pC: [pi_c[0], pi_c[1]]
            pC = [int(pi_c[0]), int(pi_c[1])]
            
            # Public signals
            pubSignals = [int(sig) for sig in public_signals]
            
            return pA, pB, pC, pubSignals
            
        except (ValueError, KeyError, IndexError, TypeError):
            return None
    
    def prove_redaction(self, public_inputs: Dict[str, Any], private_inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate complete redaction proof with formatted calldata."""
        # Generate witness
        witness_path = self.generate_witness(public_inputs, private_inputs)
        if not witness_path:
            return None
            
        try:
            # Generate proof
            proof_result = self.prove(witness_path)
            if not proof_result:
                return None
                
            proof, public_signals = proof_result
            
            # Verify proof off-chain
            if not self.verify_proof(proof, public_signals):
                return None
                
            # Format calldata
            calldata = self.format_calldata(proof, public_signals)
            if not calldata:
                return None
                
            pA, pB, pC, pubSignals = calldata
            
            return {
                "proof": proof,
                "public_signals": public_signals,
                "calldata": {
                    "pA": pA,
                    "pB": pB,
                    "pC": pC,
                    "pubSignals": pubSignals
                },
                "verified": True
            }
            
        finally:
            # Clean up witness file
            if witness_path and witness_path.exists():
                witness_path.unlink(missing_ok=True)

    def format_proof_for_solidity(self, proof: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format proof for Solidity smart contract verification.
        
        Returns proof components in a format suitable for smart contract calls.
        """
        if not proof:
            return None
            
        try:
            # Check if proof is already in Solidity format (mock proof format)
            if "a" in proof and "b" in proof and "c" in proof:
                # Already in Solidity format, just ensure publicSignals exists
                formatted_proof = proof.copy()
                if "publicSignals" not in formatted_proof:
                    formatted_proof["publicSignals"] = []
                return formatted_proof
            
            # Extract proof components from snarkjs format
            pi_a = proof.get("pi_a", [])
            pi_b = proof.get("pi_b", [])
            pi_c = proof.get("pi_c", [])
            
            if not (isinstance(pi_a, list) and isinstance(pi_b, list) and isinstance(pi_c, list)):
                return None
                
            # Format for Solidity verifier with expected field names
            formatted_proof = {
                "a": [int(pi_a[0]), int(pi_a[1])],  # Drop third coordinate (always 1)
                "b": [
                    [int(pi_b[0][1]), int(pi_b[0][0])],  # Swap G2 limbs
                    [int(pi_b[1][1]), int(pi_b[1][0])]
                ],
                "c": [int(pi_c[0]), int(pi_c[1])],
                "publicSignals": []  # Will be filled by caller if needed
            }
            
            return formatted_proof
            
        except (ValueError, KeyError, IndexError, TypeError):
            return None


# Backward compatibility aliases
RealSnarkClient = SnarkClient
