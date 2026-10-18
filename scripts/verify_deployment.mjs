// Read-only: source equality AND successful finalized execution, no wallet.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';

const root = resolve(import.meta.dirname, '..');
const manifest = JSON.parse(readFileSync(resolve(root, 'deployment.json')));
const evidence = JSON.parse(readFileSync(resolve(root, 'evidence/network.json')));
const client = createClient({chain:studionet});
async function rpcRead(operation) {
  for (let attempt = 0; ; attempt++) {
    try { return await operation(); }
    catch (error) {
      if (attempt >= 2) throw error;
      console.log('Read-only RPC request interrupted; retrying.');
      await new Promise(resolve => setTimeout(resolve, 2000 * (attempt + 1)));
    }
  }
}
assert.equal(manifest.network, 'studionet');
assert.equal(manifest.chain_id, 61999);
assert.equal(evidence[0].label, 'deploy');
assert.equal(evidence[0].hash, manifest.deployment_transaction);
const sha256 = data => createHash('sha256').update(data).digest('hex');
const local = readFileSync(resolve(root, manifest.source_path));
const remote = Buffer.from(await rpcRead(() => client.getContractCode(manifest.address)));
assert(local.equals(remote), 'Source differs byte-for-byte: redeploy before submitting');
assert.equal(sha256(local), manifest.source_sha256);
assert.equal(sha256(remote), manifest.deployed_source_sha256);
for (const item of evidence) {
  const tx = await rpcRead(() => client.getTransaction({hash:item.hash}));
  const status = tx.status_name ?? tx.statusName;
  const execution = tx.consensus_data?.leader_receipt?.[0]?.execution_result ?? tx.txExecutionResultName;
  assert.equal(status, 'FINALIZED', `${item.label} has not finalized`);
  assert.equal(execution, 'SUCCESS', `${item.label} execution failed`);
  assert.equal(tx.recipient.toLowerCase(), manifest.address.toLowerCase(), `${item.label} targets another contract`);
  console.log(`${item.label}: FINALIZED / SUCCESS ${item.hash}`);
}
const recorded = JSON.parse(readFileSync(resolve(root, 'evidence/state.json')));
const current = await rpcRead(() => client.readContract({address:manifest.address,functionName:'get_document',args:[1],jsonSafeReturn:true}));
assert.deepEqual(current, recorded.document, 'Live document head differs from recorded evidence');
for (let revision = 0; revision <= current.head; revision++) {
  const fresh = await rpcRead(() => client.readContract({address:manifest.address,functionName:'get_revision',args:[1,revision],jsonSafeReturn:true}));
  assert.deepEqual(fresh, recorded.revisions[revision], 'Live revision differs from recorded history');
}
for (const item of recorded.patches) {
  const fresh = await rpcRead(() => client.readContract({address:manifest.address,functionName:'get_patch',args:[1,item.payload.id],jsonSafeReturn:true}));
  // An expired OPEN patch can later be permissionlessly closed. Its committed
  // payload must remain identical; lifecycle state is checked for applied ones.
  assert.deepEqual(fresh.payload, item.payload);
  assert.equal(fresh.digest, item.digest);
  if (item.status === 'APPLIED') assert.equal(fresh.status, 'APPLIED');
}
for (const item of recorded.assessments) {
  const fresh = await rpcRead(() => client.readContract({address:manifest.address,functionName:'get_assessment',args:[1,item.payload.id],jsonSafeReturn:true}));
  assert.deepEqual(fresh, item);
}
console.log('Final live head and revision history match recorded evidence.');
// Preserve and independently verify the conservative rejection from the pilot.
const pilot = JSON.parse(readFileSync(resolve(root, 'evidence/pilot-rejection.json')));
assert(local.equals(Buffer.from(await rpcRead(() => client.getContractCode(pilot.manifest.address)))));
for (const item of pilot.receipts) {
  const tx = await rpcRead(() => client.getTransaction({hash:item.hash}));
  assert.equal(tx.status_name ?? tx.statusName, 'FINALIZED');
  assert.equal(tx.consensus_data?.leader_receipt?.[0]?.execution_result ?? tx.txExecutionResultName, 'SUCCESS');
  assert.equal(tx.recipient.toLowerCase(), pilot.manifest.address.toLowerCase());
}
for (const item of pilot.assessments) {
  const fresh = await rpcRead(() => client.readContract({address:pilot.manifest.address,functionName:'get_assessment',args:[1,item.payload.id],jsonSafeReturn:true}));
  assert.deepEqual(fresh, item);
}
console.log('Pilot conservative rejection and its receipts also verified.');
console.log(`Verified ${manifest.address}; SHA-256 ${sha256(local)}; ${evidence.length} successful transactions.`);
