"use server"
import { auth } from "@/util/auth";
import prisma from "@/util/prisma";
import { Result, tryCatch } from "@/util/try-catch";
import { headers } from "next/headers";

async function checkUserPatternLimit(userID: string): Promise<Result<boolean, string>> {
  const missionLimit = 50

  const userMissionCount = await tryCatch<number>(
    prisma.pattern.count({ where: { userId: userID } })
  )

  if (userMissionCount.error !== null)
    return { data: null, error: "Failed to check mission count for user" }

  if (userMissionCount.data >= missionLimit)
    return { data: null, error: `Max number of missions for user has been reached (limit of ${missionLimit})` }

  return { data: true, error: null }
}


export async function createNew(title: string, data?: string) {
  const userData = await tryCatch(auth.api.getSession({ headers: await headers() }))
  if (userData.error !== null) {
    return { error: "Could not authenticate", data: null }
  }

  const userID = userData.data?.user.id
  if (!userID) {
    return { error: "User not authenticated", data: null }
  }

  const missionLimitResult = await checkUserPatternLimit(userID)
  if (missionLimitResult.error !== null) return missionLimitResult

  const res = await tryCatch(prisma.pattern.create({
    data: {
      title: title,
      data: data ?? `from gridmas import *
def draw():
    pass`,
      userId: userID,
    }
  }))

  if (res.error !== null) {
    return { error: "Could not create pattern", data: null }
  }

  return { data: res.data, error: null }
}

export async function savePattern(id: string, data: string): Promise<Result<boolean, string>> {
  let userData = await tryCatch(auth.api.getSession({ headers: await headers() }))
  if (userData.error !== null) {
    return { error: "Could not authenticate", data: null }
  }

  const userID = userData.data?.user.id
  if (!userID) {
    return { error: "User not authenticated", data: null }
  }

  const res = await tryCatch(prisma.pattern.update({
    where: { id: id, userId: userID },
    data: { data: data, modifiedAt: new Date() }
  }))
  if (res.error !== null) {
    return { error: "Could not update pattern", data: null }
  }

  return { data: true, error: null }
}

export async function deletePattern(id: string): Promise<Result<boolean, string>> {
  let userData = await tryCatch(auth.api.getSession({ headers: await headers() }))
  if (userData.error !== null) {
    return { error: "Could not authenticate", data: null }
  }

  const userID = userData.data?.user.id
  if (!userID) {
    return { error: "User not authenticated", data: null }
  }

  const res = await tryCatch(prisma.pattern.delete({
    where: { id: id, userId: userID },
  }))
  if (res.error !== null) {
    return { error: "Could not update pattern", data: null }
  }

  return { data: true, error: null }
}

export async function renamePattern(id: string, name: string): Promise<Result<boolean, string>> {
  let userData = await tryCatch(auth.api.getSession({ headers: await headers() }))
  if (userData.error !== null) {
    return { error: "Could not authenticate", data: null }
  }

  const userID = userData.data?.user.id
  if (!userID) {
    return { error: "User not authenticated", data: null }
  }

  const res = await tryCatch(prisma.pattern.update({
    where: { id: id, userId: userID }, data: { title: name, modifiedAt: new Date() }
  }))
  if (res.error !== null) {
    return { error: "Could not update pattern", data: null }
  }

  return { data: true, error: null }
}

export async function duplicatePattern(id: string, new_name: string): Promise<Result<boolean, string>> {
  let userData = await tryCatch(auth.api.getSession({ headers: await headers() }))
  if (userData.error !== null) {
    return { error: "Could not authenticate", data: null }
  }

  const userID = userData.data?.user.id
  if (!userID) {
    return { error: "User not authenticated", data: null }
  }

  const res = await tryCatch(prisma.pattern.findFirst({
    where: { id: id, userId: userID }
  }))
  if (res.error !== null || res.data === null) {
    return { error: "Could not update pattern", data: null }
  }

  const res2 = await tryCatch(prisma.pattern.create({
    data: {
      title: new_name,
      modifiedAt: new Date(),
      data: res.data?.data,
      userId: userID
    }
  }))
  if (res2.error !== null) {
    return { error: "Could not update pattern", data: null }
  }

  return { data: true, error: null }
}

