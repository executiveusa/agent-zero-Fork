// tools/docker-agent/agent.ts
import { buildDockerImage, loginToDockerRegistry, pushDockerImage, listLocalImages } from './dockerClient.js';
import { execSync } from 'child_process';

type Grade = 'SUCCESS' | 'PROGRESS' | 'FAILURE';

interface CycleResult {
  cycle: number;
  action: string;
  grade: Grade;
  errors: string[];
  nextAction: string;
}

const MAX_CYCLES = 3;
const TAG = `v${new Date().toISOString().split('T')[0].replace(/-/g, '')}`;

function runCommand(command: string, description: string): { success: boolean; output: string } {
  console.log(`\n📦 ${description}...`);
  try {
    const output = execSync(command, { encoding: 'utf-8', stdio: 'pipe' });
    console.log(`✅ ${description} succeeded!`);
    return { success: true, output };
  } catch (error: any) {
    console.log(`❌ ${description} failed!`);
    return { success: false, output: error.message };
  }
}

async function agenticDockerBuildPushLoop(): Promise<void> {
  console.log('🐳 Docker Cloud Deployment Agent Activated');
  console.log('='.repeat(50));
  console.log('');
  console.log('🎯 Mission: Build, tag, and push Docker image');
  console.log(`📦 Image: executiveusa/agent-zero-fork:${TAG}`);
  console.log('🔄 Auto-retry: Up to 3 cycles');
  console.log('🤖 Auto-fix: Docker daemon, login issues');
  console.log('');

  const results: CycleResult[] = [];

  for (let cycle = 1; cycle <= MAX_CYCLES; cycle++) {
    console.log(`\n🔄 CYCLE ${cycle}: Build and Push`);
    console.log('─'.repeat(50));

    // Step 1: Check Docker daemon
    console.log('\n🐳 Checking Docker daemon...');
    const daemonCheck = runCommand('docker ps', 'Checking Docker daemon');

    if (!daemonCheck.success) {
      console.log('❌ Docker daemon is not running!');
      console.log('');
      console.log('💡 Please start Docker Desktop and try again.');
      console.log('   Or run: docker run hello-world');
      console.log('');
      results.push({
        cycle,
        action: 'docker_check',
        grade: 'FAILURE',
        errors: ['Docker daemon not running'],
        nextAction: 'escalate',
      });
      console.log('📊 Self-Grade: ❌ FAILURE');
      continue;
    }

    console.log('✅ Docker daemon is running');

    // Step 2: List existing images
    console.log('\n📋 Checking existing images...');
    try {
      const images = await listLocalImages();
      console.log(`   Found ${images.length} existing image(s)`);
    } catch (error) {
      console.log('⚠️ Could not list images, continuing...');
    }

    // Step 3: Build image
    console.log('\n🔨 Building Docker image...');
    try {
      const buildResult = await buildDockerImage(TAG);
      console.log(`   Image ID: ${buildResult.id}`);
    } catch (error: any) {
      console.log(`❌ Build failed: ${error.message}`);

      // Auto-fix: Try removing dangling images
      if (cycle < MAX_CYCLES) {
        console.log('\n🔧 Auto-fix: Cleaning dangling images...');
        try {
          execSync('docker image prune -f', { encoding: 'utf-8', stdio: 'pipe' });
          console.log('✅ Cleaned up dangling images');

          // Retry build
          try {
            const retryResult = await buildDockerImage(TAG);
            console.log('✅ Retry build succeeded');
          } catch (retryError: any) {
            console.log(`❌ Retry build failed: ${retryError.message}`);
            results.push({
              cycle,
              action: 'build',
              grade: 'FAILURE',
              errors: [error.message],
              nextAction: 'escalate',
            });
            console.log('📊 Self-Grade: ❌ FAILURE');
            continue;
          }
        } catch (cleanError: any) {
          console.log(`⚠️ Cleanup failed: ${cleanError.message}`);
          results.push({
            cycle,
            action: 'build',
            grade: 'FAILURE',
            errors: [error.message],
            nextAction: 'escalate',
          });
          console.log('📊 Self-Grade: ❌ FAILURE');
          continue;
        }
      }
    }

    // Step 4: Login to Docker
    console.log('\n🔐 Authenticating with Docker Registry...');
    try {
      await loginToDockerRegistry();
    } catch (error: any) {
      console.log(`❌ Login failed: ${error.message}`);
      results.push({
        cycle,
        action: 'login',
        grade: 'FAILURE',
        errors: [error.message],
        nextAction: 'escalate',
      });
      console.log('📊 Self-Grade: ❌ FAILURE');
      console.log('');
      console.log('💡 Troubleshooting:');
      console.log('   - Check DOCKER_TOKEN in .env file');
      console.log('   - Verify token at: https://hub.docker.com/settings/security');
      continue;
    }

    // Step 5: Push image
    console.log('\n📤 Pushing image to Docker Hub...');
    try {
      const pushResult = await pushDockerImage(TAG);
      console.log(`   Status: ${pushResult.status}`);
      if (pushResult.digest) {
        console.log(`   Digest: ${pushResult.digest}`);
      }

      results.push({
        cycle,
        action: 'push',
        grade: 'SUCCESS',
        errors: [],
        nextAction: 'complete',
      });

      console.log('\n📊 Self-Grade: ✅ SUCCESS');
      console.log('');
      console.log('='.repeat(50));
      console.log('🎉 SUCCESS! Docker image pushed successfully!');
      console.log(`🐳 Image: executiveusa/agent-zero-fork:${TAG}`);
      console.log(`🔗 URL: https://hub.docker.com/r/executiveusa/agent-zero-fork`);
      console.log('✅ Image is now available in Docker Hub');
      console.log('='.repeat(50));
      return;
    } catch (error: any) {
      console.log(`❌ Push failed: ${error.message}`);
      results.push({
        cycle,
        action: 'push',
        grade: 'FAILURE',
        errors: [error.message],
        nextAction: 'retry',
      });
      console.log('📊 Self-Grade: ❌ FAILURE');
      console.log('Decision: Continuing to next cycle...');
    }
  }

  // If we got here, we exhausted cycles
  console.log('\n');
  console.log('='.repeat(50));
  console.log('⚠️ ESCALATION REQUIRED');
  console.log('='.repeat(50));
  console.log(`After ${MAX_CYCLES} attempts, Docker push not complete.`);
  console.log('');
  console.log('📋 Summary of attempts:');
  results.forEach((r, i) => {
    console.log(`   ${i + 1}. Cycle ${r.cycle}: ${r.action} - ${r.grade}`);
    if (r.errors.length > 0) {
      console.log(`      Errors: ${r.errors.join(', ')}`);
    }
  });
  console.log('');
  console.log('💡 Next steps:');
  console.log('   1. Check Docker daemon is running');
  console.log('   2. Verify DOCKER_USERNAME and DOCKER_TOKEN in .env');
  console.log('   3. Test login: docker login -u executiveusa');
  console.log('   4. Check Docker Hub: https://hub.docker.com/settings/security');
  console.log('   5. Try manual push: docker push executiveusa/agent-zero-fork:latest');
  console.log('');
  process.exit(1);
}

// Run the agent
agenticDockerBuildPushLoop().catch(error => {
  console.error('\n❌ Fatal error:', error);
  process.exit(1);
});
