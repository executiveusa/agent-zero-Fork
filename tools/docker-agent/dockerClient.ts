// tools/docker-agent/dockerClient.ts
import 'dotenv/config';

const DOCKER_USERNAME = process.env.DOCKER_USERNAME || 'executiveusa';
const DOCKER_TOKEN = process.env.DOCKER_TOKEN;
const IMAGE_NAME = process.env.DOCKER_IMAGE_NAME || 'agent-zero-fork';
const REGISTRY = process.env.DOCKER_REGISTRY || 'docker.io';

interface ImageBuildResponse {
  id: string;
  created: string;
  tag: string;
}

interface ImagePushResponse {
  status: string;
  pushed: boolean;
  digest?: string;
}

async function runCommand(command: string): Promise<{ success: boolean; output: string }> {
  const { execSync } = require('child_process');
  try {
    const output = execSync(command, { encoding: 'utf-8' });
    return { success: true, output };
  } catch (error: any) {
    return { success: false, output: error.message };
  }
}

export async function buildDockerImage(tag: string = 'latest'): Promise<ImageBuildResponse> {
  console.log(`\n🐳 Building Docker image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${tag}`);

  const dockerfile = './Dockerfile';
  const command = `docker build -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${tag} -t ${DOCKER_USERNAME}/${IMAGE_NAME}:latest -f ${dockerfile} .`;

  const result = await runCommand(command);

  if (!result.success) {
    throw new Error(`Docker build failed: ${result.output}`);
  }

  console.log(`   ✅ Image built successfully`);
  console.log(`   📦 Tag: ${DOCKER_USERNAME}/${IMAGE_NAME}:${tag}`);

  return {
    id: `${DOCKER_USERNAME}/${IMAGE_NAME}:${tag}`,
    created: new Date().toISOString(),
    tag: tag,
  };
}

export async function loginToDockerRegistry(): Promise<boolean> {
  if (!DOCKER_TOKEN) {
    throw new Error('DOCKER_TOKEN not found in .env');
  }

  console.log(`\n🔐 Logging in to Docker Registry...`);
  console.log(`   Registry: ${REGISTRY}`);
  console.log(`   Username: ${DOCKER_USERNAME}`);

  const command = `echo "${DOCKER_TOKEN}" | docker login -u ${DOCKER_USERNAME} --password-stdin ${REGISTRY}`;

  const result = await runCommand(command);

  if (!result.success) {
    throw new Error(`Docker login failed: ${result.output}`);
  }

  console.log(`   ✅ Successfully logged in to ${REGISTRY}`);
  return true;
}

export async function pushDockerImage(tag: string = 'latest'): Promise<ImagePushResponse> {
  console.log(`\n📤 Pushing Docker image to registry...`);

  const fullTag = `${DOCKER_USERNAME}/${IMAGE_NAME}:${tag}`;
  const command = `docker push ${fullTag}`;

  const result = await runCommand(command);

  if (!result.success) {
    throw new Error(`Docker push failed: ${result.output}`);
  }

  console.log(`   ✅ Image pushed successfully`);
  console.log(`   🌐 Registry: ${REGISTRY}`);
  console.log(`   📦 Image: ${fullTag}`);

  return {
    status: 'pushed',
    pushed: true,
    digest: fullTag,
  };
}

export async function listLocalImages(): Promise<string[]> {
  console.log(`\n📋 Checking local Docker images...`);

  const command = `docker images ${DOCKER_USERNAME}/${IMAGE_NAME} --format "table {{.Repository}}:{{.Tag}} {{.Size}}"`;

  const result = await runCommand(command);

  if (!result.success) {
    console.log(`⚠️ Could not list images`);
    return [];
  }

  const images = result.output
    .split('\n')
    .filter(line => line.trim() && !line.includes('REPOSITORY'))
    .map(line => line.trim());

  if (images.length > 0) {
    console.log(`   Found ${images.length} image(s):`);
    images.forEach(img => console.log(`     • ${img}`));
  } else {
    console.log(`   No images found`);
  }

  return images;
}

export async function getImageDigest(tag: string = 'latest'): Promise<string | null> {
  const command = `docker inspect ${DOCKER_USERNAME}/${IMAGE_NAME}:${tag} --format="{{.RepoDigests}}"`;

  const result = await runCommand(command);

  if (!result.success) {
    return null;
  }

  return result.output.trim();
}
