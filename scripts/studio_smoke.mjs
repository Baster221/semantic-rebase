// MUTATING: fresh gasless StudioNet demo. --record saves public evidence only.
// Three independent demonstration keys remain exclusively in process memory.
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {createClient, createAccount} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';

const root=resolve(import.meta.dirname,'..');
const sourcePath='contracts/semantic_rebase.py';
const code=readFileSync(resolve(root,sourcePath),'utf8');
const accounts=[createAccount(),createAccount(),createAccount()];
const clients=accounts.map(account=>createClient({chain:studionet,account}));
const record=process.argv.includes('--record');
const receipts=[];
const save=(name,data)=>writeFileSync(resolve(root,name),JSON.stringify(data,(_,v)=>typeof v==='bigint'?v.toString():v,2)+'\n');
let address;
async function finish(hash,label){
  console.log(`submitted ${label}: ${hash}`);
  const tx=await clients[0].waitForTransactionReceipt({hash,status:'FINALIZED',interval:7000,retries:100});
  const status=tx.status_name??tx.statusName;
  const execution=tx.consensus_data?.leader_receipt?.[0]?.execution_result??tx.txExecutionResultName;
  assert.equal(status,'FINALIZED',label);
  assert.equal(execution,'SUCCESS',`${label}: ${JSON.stringify(tx.consensus_data?.leader_receipt?.[0])}`);
  const leader=tx.consensus_data?.leader_receipt?.[0];
  receipts.push({label,hash,status,execution,result:tx.result_name??tx.resultName,
    votes:tx.consensus_data?.votes,leader_result:leader?.result,eq_outputs:leader?.eq_outputs});
  if(record)save('evidence/network.json',receipts);
  console.log(`finalized ${label}`);
  return tx;
}
const deployHash=await clients[0].deployContract({code,args:[]});
const deployment=await finish(deployHash,'deploy');
address=deployment.recipient;
assert.equal(await clients[0].getContractCode(address),code);
const read=(functionName,args)=>clients[0].readContract({address,functionName,args,jsonSafeReturn:true});
const write=async(idx,functionName,args,label=functionName)=>finish(await clients[idx].writeContract({address,functionName,args,value:0n}),label);
if(record){
  const hash=createHash('sha256').update(code).digest('hex');
  save('deployment.json',{network:'studionet',chain_id:61999,rpc:'https://studio.genlayer.com/api',address,
    explorer:`https://explorer-studio.genlayer.com/address/${address}`,deployment_transaction:deployHash,
    deployer:accounts[0].address,source_path:sourcePath,source_sha256:hash,deployed_source_sha256:hash,
    byte_for_byte_match:true,runner:'py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6',
    deployment_status:'FINALIZED',deployment_execution:'SUCCESS',verified_at:new Date().toISOString()});
}
const base=[
 'Event format: This workshop is held online only.',
 'Registration: Participants must register before attending the workshop.',
 'Session time: Starts at 10:00 UTC.',
];
await write(0,'create_document',['Workshop logistics',JSON.stringify(base),JSON.stringify([accounts[1].address])],'create sectioned document');
await write(0,'prepare_patch',[1,0,JSON.stringify([{section:0,text:'Event format: This workshop is held in person only at Room A; no online access is offered.'}]),86400],'prepare concurrent format change');
await write(1,'prepare_patch',[1,0,JSON.stringify([{section:1,text:'Registration: Register to receive the online meeting link. Attendance is online only; do not travel to a physical venue.'}]),86400],'prepare cross-section dependent branch');
await write(1,'prepare_patch',[1,0,JSON.stringify([{section:2,text:'Session time: Starts at 11:00 UTC.'}]),86400],'prepare independent time branch');
const head0=(await read('get_document',[1])).head_digest;
await write(1,'assess',[1,3,head0],'assess time patch against initial head');
assert.equal((await read('get_assessment',[1,1])).payload.status,'SAFE');
await write(1,'assess',[1,1,head0],'assess format patch');
assert.equal((await read('get_assessment',[1,2])).payload.status,'SAFE');
await write(2,'commit',[1,2],'commit in-person format revision');
const head1=(await read('get_document',[1])).head_digest;
assert.notEqual(head0,head1);
await write(1,'assess',[1,2,head1],'detect semantic conflict across untouched section IDs');
assert.equal((await read('get_assessment',[1,3])).payload.status,'SEMANTIC_CONFLICT');
await write(1,'assess',[1,3,head1],'reassess independent time patch against new head');
assert.equal((await read('get_assessment',[1,4])).payload.status,'SAFE');
await write(2,'commit',[1,4],'commit safe rebased time patch');
const document=await read('get_document',[1]);
const revisions=await Promise.all([0,1,2].map(i=>read('get_revision',[1,i])));
assert.equal(document.head,2);
assert.match(revisions[2].payload.sections[0],/in person only/);
assert.equal(revisions[2].payload.sections[2],'Session time: Starts at 11:00 UTC.');
const patches=await Promise.all([1,2,3].map(i=>read('get_patch',[1,i])));
const assessments=await Promise.all([1,2,3,4].map(i=>read('get_assessment',[1,i])));
if(record)save('evidence/state.json',{document,revisions,patches,assessments,
  initialAssessmentNowStale:assessments[0].payload.head_digest!==document.head_digest,
  roles:{owner:accounts[0].address,editorAndReviewer:accounts[1].address,permissionlessCommitter:accounts[2].address}});
console.log(`Semantic Rebase smoke passed: ${address}. No signing keys were persisted.`);
