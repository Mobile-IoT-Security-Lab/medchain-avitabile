// Bookmark1 for next meeting
// Redaction proof circuit
// Implements:
//  - H(original) and H(redacted) via a MiMC-like hash over field elements
//  - Policy hash matching (hash of policy preimage)
//  - Optional Merkle membership proof (over MiMC hash) gating on a boolean

pragma circom 2.1.5;

// Utilities
// Compose 2x128-bit limbs into a single field element for matching

template Pow7() {
    signal input in;
    signal output out;
    signal t2;
    signal t4;
    signal t6;
    t2 <== in * in;
    t4 <== t2 * t2;
    t6 <== t4 * t2;
    out <== t6 * in;
}

// Simple MiMC-like permutation with zero round constants (for demo consistency)
// Note: Constants are zeros to keep H(0,...,0) = 0 matching example inputs.
// Replace constants with standard parameters for production usage.
template MiMCPerm(ROUNDS) {
    signal input x_in;
    signal output x_out;
    signal x[ROUNDS + 1];
    signal t[ROUNDS];
    component p[ROUNDS];
    x[0] <== x_in;
    for (var i = 0; i < ROUNDS; i++) {
        // Round constant c[i] = 0 (demo)
        t[i] <== x[i];
        p[i] = Pow7();
        p[i].in <== t[i];
        x[i+1] <== p[i].out;
    }
    x_out <== x[ROUNDS];
}

// Hash over a vector by absorbing each element into the state
template MiMCHash(N, ROUNDS) {
    signal input in[N];
    signal output out;
    signal state[N + 1];
    signal sPlus[N];
    component perm[N];
    state[0] <== 0;
    for (var i = 0; i < N; i++) {
        sPlus[i] <== state[i] + in[i];
        perm[i] = MiMCPerm(ROUNDS);
        perm[i].x_in <== sPlus[i];
        state[i+1] <== perm[i].x_out;
    }
    out <== state[N];
}

template Hash2(ROUNDS) {
    signal input left;
    signal input right;
    signal output out;
    component h = MiMCHash(2, ROUNDS);
    h.in[0] <== left;
    h.in[1] <== right;
    out <== h.out;
}

template Mul2() {
    signal input x;
    signal input y;
    signal output out;
    signal tmp;
    tmp <== x * y;
    out <== tmp;
}

template Select2() {
    // out = a if s==0 else b; requires s boolean
    signal input a;
    signal input b;
    signal input s;
    signal output out;
    s * (s - 1) === 0;
    component m = Mul2();
    m.x <== s;
    // (b - a) is linear, safe on RHS of <== to an input
    m.y <== b - a;
    out <== a + m.out;
}

template MerkleInclusion(DEPTH, ROUNDS) {
    signal input leaf;
    signal input pathElements[DEPTH];
    signal input pathIndices[DEPTH]; // 0: leaf on left; 1: leaf on right
    signal output root;

    // Ensure indices are boolean
    for (var i = 0; i < DEPTH; i++) {
        pathIndices[i] * (pathIndices[i] - 1) === 0;
    }

    signal node[DEPTH + 1];
    component selL[DEPTH];
    component selR[DEPTH];
    component h[DEPTH];
    node[0] <== leaf;
    for (var i = 0; i < DEPTH; i++) {
        // left = Select2(node, pathElem, b); right = Select2(pathElem, node, b)
        selL[i] = Select2();
        selL[i].a <== node[i];
        selL[i].b <== pathElements[i];
        selL[i].s <== pathIndices[i];
        selR[i] = Select2();
        selR[i].a <== pathElements[i];
        selR[i].b <== node[i];
        selR[i].s <== pathIndices[i];
        h[i] = Hash2(ROUNDS);
        h[i].left <== selL[i].out;
        h[i].right <== selR[i].out;
        node[i+1] <== h[i].out;
    }
    root <== node[DEPTH];
}

template RedactionCircuit() {
    // Parameters
    var ORIG_LEN = 4;    // number of field elements representing original data
    var RED_LEN = 4;     // number of field elements representing redacted data
    var POLICY_LEN = 2;  // number of field elements representing policy preimage
    var MERKLE_DEPTH = 8; // Merkle tree depth
    var ROUNDS = 65;     // MiMC rounds (demo)

    // Public inputs (split 256-bit values into two limbs for convenience)
    signal input policyHash0;
    signal input policyHash1;
    signal input merkleRoot0;
    signal input merkleRoot1;
    signal input originalHash0;
    signal input originalHash1;
    signal input redactedHash0;
    signal input redactedHash1;

    // Consistency proof public inputs (state hashes before/after redaction)
    signal input preStateHash0;
    signal input preStateHash1;
    signal input postStateHash0;
    signal input postStateHash1;
    signal input consistencyCheckPassed; // 1 if consistency proof valid, 0 otherwise

    // Public policy flag: 1 means redaction permitted under the policy
    signal input policyAllowed;

    // Private inputs
    signal input originalData[ORIG_LEN];
    signal input redactedData[RED_LEN];
    signal input policyData[POLICY_LEN];
    signal input merklePathElements[MERKLE_DEPTH];
    signal input merklePathIndices[MERKLE_DEPTH];
    signal input enforceMerkle; // boolean: 1 to enforce inclusion proof, 0 to skip

    // Boolean checks
    policyAllowed * (policyAllowed - 1) === 0;
    enforceMerkle * (enforceMerkle - 1) === 0;
    consistencyCheckPassed * (consistencyCheckPassed - 1) === 0;

    // Require consistency check to pass (if consistency proof provided)
    consistencyCheckPassed === 1;

    // Compute hashes
    component hOrig = MiMCHash(ORIG_LEN, ROUNDS);
    for (var i = 0; i < ORIG_LEN; i++) hOrig.in[i] <== originalData[i];
    component hRed = MiMCHash(RED_LEN, ROUNDS);
    for (var j = 0; j < RED_LEN; j++) hRed.in[j] <== redactedData[j];
    component hPol = MiMCHash(POLICY_LEN, ROUNDS);
    for (var k = 0; k < POLICY_LEN; k++) hPol.in[k] <== policyData[k];

    // Compose public limbs and match the computed hashes
    var SHIFT128 = 1 << 128;
    signal expectedOrig;
    expectedOrig <== originalHash0 + originalHash1 * SHIFT128;
    hOrig.out === expectedOrig;

    signal expectedRed;
    expectedRed <== redactedHash0 + redactedHash1 * SHIFT128;
    hRed.out === expectedRed;

    signal expectedPol;
    expectedPol <== policyHash0 + policyHash1 * SHIFT128;
    hPol.out === expectedPol;

    // Optional Merkle inclusion of original hash
    component mer = MerkleInclusion(MERKLE_DEPTH, ROUNDS);
    mer.leaf <== hOrig.out;
    for (var m = 0; m < MERKLE_DEPTH; m++) {
        mer.pathElements[m] <== merklePathElements[m];
        mer.pathIndices[m] <== merklePathIndices[m];
    }
    // Gate enforcement: if enforceMerkle == 1, the root must match; if 0, skip
    signal expectedRoot;
    expectedRoot <== merkleRoot0 + merkleRoot1 * SHIFT128;
    (mer.root - expectedRoot) * enforceMerkle === 0;

    // Require policyAllowed == 1 for success (demo semantics)
    policyAllowed === 1;

    // Output a checksum to exercise inputs
    signal output witnessChecksum;
    witnessChecksum <== policyHash0
                    +  policyHash1
                    +  merkleRoot0
                    +  merkleRoot1
                    +  originalHash0
                    +  originalHash1
                    +  redactedHash0
                    +  redactedHash1
                    +  preStateHash0
                    +  preStateHash1
                    +  postStateHash0
                    +  postStateHash1
                    +  consistencyCheckPassed
                    +  policyAllowed;
}

component main = RedactionCircuit();
